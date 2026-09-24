"""Shared LCEL construction. HTTP contracts and retry policy belong to the API."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


def _create_model(*, api_key: str, model: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        vertexai=False,
        max_output_tokens=300,
        temperature=0.3,
        thinking_budget=0,
        timeout=10,
        max_retries=0,  # The API owns the three-attempt retry budget.
    )


def generate_text(*, api_key: str, model: str, contents: str) -> str:
    # Bind content as a value, never as a template: JSON braces in simulation
    # context and user messages must remain literal. Preserve the original prompt.
    prompt_template = ChatPromptTemplate.from_messages([("human", "{contents}")])
    llm = _create_model(api_key=api_key, model=model)
    chain = prompt_template | llm | StrOutputParser()
    return chain.invoke({"contents": contents}).strip()
