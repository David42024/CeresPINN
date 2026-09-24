"""Exercise real LCEL composition with a deterministic model, without API calls."""
import json

import httpx
import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

import backend.llm as llm_mod


def test_lcel_preserves_literal_context_and_parses_message(monkeypatch):
    captured = {}

    def respond(prompt):
        captured["messages"] = prompt.to_messages()
        return AIMessage(content="  Resultado de prueba.  ")

    def create(**kwargs):
        captured.update(kwargs)
        return RunnableLambda(respond)

    monkeypatch.setattr(llm_mod, "_create_model", create)
    contents = 'Contexto: {"projectedYieldKgHa": 8778}\nPregunta: {no_es_variable}'
    result = llm_mod.generate_text(api_key="test-key", model="test-model", contents=contents)
    assert result == "Resultado de prueba."
    assert captured["messages"][0].content == contents
    assert captured["model"] == "test-model"
    assert captured["api_key"] == "test-key"


def test_openai_configuration_without_network():
    model = llm_mod._create_model(api_key="test-only-key", model="gpt-5-nano")
    assert model.model_name == "gpt-5-nano"
    assert model.use_responses_api is True
    assert model.reasoning == {"effort": "minimal"}
    assert model.max_tokens == 512
    assert model.temperature is None
    assert model.max_retries == 0
    assert model.request_timeout == 30
    assert model.store is False


def test_openai_responses_request_has_supported_gpt5_parameters(monkeypatch):
    captured = {}
    real_model = llm_mod.ChatOpenAI

    def inspect_request(request):
        captured["path"] = request.url.path
        captured["payload"] = json.loads(request.content)
        return httpx.Response(400, json={"error": {"message": "test stop", "type": "invalid_request_error"}})

    client = httpx.Client(transport=httpx.MockTransport(inspect_request))
    monkeypatch.setattr(
        llm_mod,
        "ChatOpenAI",
        lambda **kwargs: real_model(**kwargs, http_client=client),
    )
    with pytest.raises(Exception):
        llm_mod.generate_text(
            api_key="test-only-key", model="gpt-5-nano", contents="Resumen: {\"yield\": 8000}"
        )

    assert captured["path"] == "/v1/responses"
    assert captured["payload"]["model"] == "gpt-5-nano"
    assert captured["payload"]["reasoning"] == {"effort": "minimal"}
    assert captured["payload"]["max_output_tokens"] == 512
    assert captured["payload"]["store"] is False
    assert "temperature" not in captured["payload"]


@pytest.mark.parametrize("path,body,field", [
    ("/api/chatbot", {"message": "Hola", "context": {"projectedYieldKgHa": 8778}}, "reply"),
    ("/api/reports/ai-summary", {"scenario": "SSP2-4.5", "simulation_summary": {"projectedYieldKgHa": 8778}}, "summary"),
])
def test_endpoints_execute_lcel_and_retry(test_client, monkeypatch, path, body, field):
    import backend.app as app_mod
    prompts, delays = [], []

    def respond(prompt):
        prompts.append(prompt.to_messages()[0].content)
        if len(prompts) < 3:
            raise RuntimeError("503 UNAVAILABLE")
        return AIMessage(content="Resultado de prueba.")

    monkeypatch.setenv("OPENAI_API_KEY", "test-only-key")
    monkeypatch.setattr(llm_mod, "_create_model", lambda **kw: RunnableLambda(respond))
    monkeypatch.setattr(app_mod.time, "sleep", delays.append)
    response = test_client.post(path, json=body)
    assert response.status_code == 200
    assert response.json()[field] == "Resultado de prueba."
    assert len(prompts) == 3
    assert delays == [1.5, 3.0]
    assert "8778" in prompts[-1]


@pytest.mark.parametrize("error,attempts", [("503 UNAVAILABLE secret", 3), ("401 secret", 1)])
@pytest.mark.parametrize("path,body", [
    ("/api/chatbot", {"message": "Hola"}),
    ("/api/reports/ai-summary", {"scenario": "SSP2-4.5", "simulation_summary": {"yield": 8000}}),
])
def test_provider_failures_are_bounded_and_sanitized(test_client, monkeypatch, error, attempts, path, body):
    import backend.app as app_mod
    calls = []

    def fail(prompt):
        calls.append(prompt)
        raise RuntimeError(error)

    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setattr(llm_mod, "_create_model", lambda **kw: RunnableLambda(fail))
    monkeypatch.setattr(app_mod.time, "sleep", lambda _: None)
    response = test_client.post(path, json=body)
    assert response.status_code == 502
    assert "secret" not in response.text
    assert len(calls) == attempts


def test_summary_missing_key_and_empty_response(test_client, monkeypatch):
    body = {"scenario": "SSP2-4.5", "simulation_summary": {"yield": 8000}}
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = test_client.post("/api/reports/ai-summary", json=body)
    assert response.status_code == 503
    assert response.json()["summary"] is None
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm_mod, "_create_model", lambda **kw: RunnableLambda(lambda _: AIMessage(content=" ")))
    response = test_client.post("/api/reports/ai-summary", json=body)
    assert response.status_code == 502
    assert response.json()["summary"] is None


@pytest.mark.parametrize("body", [
    {},
    {"scenario": "SSP2-4.5", "simulation_summary": {}},
    {"scenario": " ", "simulation_summary": {"yield": 8000}},
    {"scenario": "SSP2-4.5", "simulation_summary": {"text": "x" * 12_001}},
])
def test_invalid_summaries_rejected_before_model_call(test_client, monkeypatch, body):
    def unexpected(**kwargs):
        pytest.fail("Invalid input reached the model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm_mod, "_create_model", unexpected)
    assert test_client.post("/api/reports/ai-summary", json=body).status_code == 422
