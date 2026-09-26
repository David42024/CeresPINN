"""Server-side execution of the visual CeresPINN flows in Langflow.

Only the backend talks to Langflow. Browser clients never receive its API key.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import quote, urlsplit
from uuid import uuid4

import requests


class LangflowConfigurationError(RuntimeError):
    pass


class LangflowExecutionError(RuntimeError):
    def __init__(self, status_code: int | None = None):
        super().__init__("Langflow execution failed")
        self.status_code = status_code


@dataclass(frozen=True)
class LangflowConfig:
    base_url: str
    api_key: str
    chatbot_flow_id: str


def langflow_requested() -> bool:
    """A URL explicitly opts into Langflow; partial settings never silently fall back."""
    return bool(os.getenv("LANGFLOW_BASE_URL", "").strip())


def config_from_env() -> LangflowConfig:
    base_url = os.getenv("LANGFLOW_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("LANGFLOW_API_KEY", "").strip()
    chatbot_flow_id = os.getenv("LANGFLOW_CHATBOT_FLOW_ID", "").strip()
    parsed = urlsplit(base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise LangflowConfigurationError("LANGFLOW_BASE_URL must be a bare HTTP(S) origin")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise LangflowConfigurationError("Remote Langflow must use HTTPS")
    if not api_key or not chatbot_flow_id:
        raise LangflowConfigurationError("Langflow URL, API key and chatbot flow ID are required")
    return LangflowConfig(base_url, api_key, chatbot_flow_id)


def _response_text(body: object) -> str:
    if not isinstance(body, dict):
        raise LangflowExecutionError(502)
    outputs = body.get("outputs")
    if not isinstance(outputs, list):
        raise LangflowExecutionError(502)
    for item in outputs:
        for output in item.get("outputs", []) if isinstance(item, dict) else []:
            if not isinstance(output, dict):
                continue
            results = output.get("results")
            if not isinstance(results, dict):
                continue
            message = results.get("message")
            if isinstance(message, dict) and isinstance(message.get("text"), str):
                result = message["text"].strip()
                if result:
                    return result
    raise LangflowExecutionError(502)


def run_chatbot_flow(*, input_value: str, config: LangflowConfig | None = None) -> str:
    config = config or config_from_env()
    url = f"{config.base_url}/api/v1/run/{quote(config.chatbot_flow_id, safe='')}"
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json", "x-api-key": config.api_key},
            json={
                "input_value": input_value,
                "input_type": "chat",
                "output_type": "chat",
                "session_id": f"cerespinn-{uuid4().hex}",
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        raise LangflowExecutionError(503) from exc
    if not response.ok:
        raise LangflowExecutionError(response.status_code)
    try:
        return _response_text(response.json())
    except ValueError as exc:
        raise LangflowExecutionError(502) from exc
