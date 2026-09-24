"""Shared LCEL construction. HTTP contracts and retry policy belong to the API."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def _create_model(*, api_key: str, model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        use_responses_api=True,
        reasoning={"effort": "minimal"},
        max_tokens=512,
        timeout=30,
        max_retries=0,  # The API owns the three-attempt retry budget.
        store=False,
    )


def generate_text(*, api_key: str, model: str, contents: str) -> str:
    # Bind content as a value, never as a template: JSON braces in simulation
    # context and user messages must remain literal. Preserve the original prompt.
    prompt_template = ChatPromptTemplate.from_messages([("human", "{contents}")])
    llm = _create_model(api_key=api_key, model=model)
    chain = prompt_template | llm | StrOutputParser()
    return chain.invoke({"contents": contents}).strip()
