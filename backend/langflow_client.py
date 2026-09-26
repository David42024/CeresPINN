"""Server-side execution of the visual CeresPINN flows in Langflow.

This module now uses `langflow.load` to execute a local .json flow directly
in memory instead of making REST requests to an external Langflow server.
"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass

try:
    from langflow.load import run_flow_from_json
    LANGFLOW_AVAILABLE = True
except ImportError:
    LANGFLOW_AVAILABLE = False


class LangflowConfigurationError(RuntimeError):
    pass


class LangflowExecutionError(RuntimeError):
    def __init__(self, status_code: int | None = None, message: str = "Langflow execution failed"):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class LangflowConfig:
    pass


def langflow_requested() -> bool:
    """A URL explicitly opts into Langflow; or if the local JSON exists."""
    # Consider requested if the user placed the JSON file in backend/
    json_path = Path(__file__).parent / "chatbot_flow.json"
    return json_path.exists()


def config_from_env() -> LangflowConfig:
    """Returns an empty config since we run locally from JSON now."""
    json_path = Path(__file__).parent / "chatbot_flow.json"
    if not json_path.exists():
        raise LangflowConfigurationError("No se encontró el archivo chatbot_flow.json en backend/")
    return LangflowConfig()


def run_chatbot_flow(*, input_value: str, config: LangflowConfig | None = None) -> str:
    """Run the chatbot flow headless in the same process."""
    if not LANGFLOW_AVAILABLE:
        raise LangflowExecutionError(503, "Langflow module is not installed. Add it to requirements.txt.")
        
    json_path = Path(__file__).parent / "chatbot_flow.json"
    if not json_path.exists():
        raise LangflowExecutionError(500, "Flow JSON not found.")
        
    try:
        # Run local langflow file
        result = run_flow_from_json(
            flow=str(json_path),
            input_value=input_value,
            fallback_to_env_vars=True,
            tweaks={}
        )
        
        # Depending on your specific flow, the output structure might change.
        # Generally, it looks like this for a Chat Output node:
        return result[0].outputs[0].results["message"].text
    except Exception as exc:
        print(f"Error running local Langflow: {exc}")
        raise LangflowExecutionError(500, str(exc)) from exc
