"""Minimal watsonx.ai Chat API client."""

import os
from pathlib import Path

from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference


EXPECTED_WATSONX_URL = "https://eu-de.ml.cloud.ibm.com"
EXPECTED_MODEL_ID = "meta-llama/llama-3-3-70b-instruct"

CHAT_PARAMETERS = {
    "temperature": 0,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "max_completion_tokens": 512,
}

JSON_RESPONSE_FORMAT = {"type": "json_object"}

PARAMETER_MAPPING = {
    "temperature": "temperature",
    "top_p": "top_p",
    "frequency_penalty": "frequency_penalty",
    "presence_penalty": "presence_penalty",
    "generation_token_limit": "max_completion_tokens",
    "random_seed": "unset",
    "stop_sequences": "none",
    "ai_guardrails": "not enabled",
}


def chat_parameters(json_response_mode=False):
    parameters = dict(CHAT_PARAMETERS)
    if json_response_mode:
        parameters["response_format"] = dict(JSON_RESPONSE_FORMAT)
    return parameters


def project_root():
    return Path(__file__).resolve().parents[1]


def load_effective_config(root=None):
    """Load non-secret watsonx config; never returns the API key value."""

    root_path = Path(root) if root is not None else project_root()
    dotenv_path = root_path / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=False)

    return {
        "env_exists": dotenv_path.exists(),
        "api_key_present": bool(os.environ.get("WATSONX_APIKEY")),
        "url": os.environ.get("WATSONX_URL"),
        "project_id": os.environ.get("WATSONX_PROJECT_ID"),
        "model_id": os.environ.get("WATSONX_MODEL_ID"),
        "parameter_mapping": dict(PARAMETER_MAPPING),
        "chat_parameters": dict(CHAT_PARAMETERS),
        "json_response_format": dict(JSON_RESPONSE_FORMAT),
    }


def validate_effective_config(config):
    missing = []
    mismatches = []

    for name, key in (
        ("WATSONX_APIKEY", "api_key_present"),
        ("WATSONX_URL", "url"),
        ("WATSONX_PROJECT_ID", "project_id"),
        ("WATSONX_MODEL_ID", "model_id"),
    ):
        value = config.get(key)
        if value is None or value is False or value == "":
            missing.append(name)

    expected = {
        "WATSONX_URL": (config.get("url"), EXPECTED_WATSONX_URL),
        "WATSONX_MODEL_ID": (config.get("model_id"), EXPECTED_MODEL_ID),
    }
    for name, (actual, expected_value) in expected.items():
        if actual and actual != expected_value:
            mismatches.append({"name": name, "expected": expected_value, "actual": actual})

    return {"valid": not missing and not mismatches, "missing": missing, "mismatches": mismatches}


def create_model(config=None):
    config = config or load_effective_config()
    validation = validate_effective_config(config)
    if not validation["valid"]:
        missing = ", ".join(validation["missing"])
        mismatched = ", ".join(item["name"] for item in validation["mismatches"])
        parts = []
        if missing:
            parts.append(f"missing: {missing}")
        if mismatched:
            parts.append(f"mismatched: {mismatched}")
        raise RuntimeError("Invalid watsonx configuration (" + "; ".join(parts) + ").")

    credentials = Credentials(
        url=config["url"],
        api_key=os.environ.get("WATSONX_APIKEY"),
    )
    return ModelInference(
        model_id=config["model_id"],
        credentials=credentials,
        project_id=config["project_id"],
        params=dict(CHAT_PARAMETERS),
    )


class WatsonxChatClient:
    def __init__(self, model=None, config=None, json_response_mode=False):
        self.config = config or load_effective_config()
        self.model = model or create_model(self.config)
        self.json_response_mode = json_response_mode

    def chat(self, messages):
        response = self.model.chat(messages=messages, params=chat_parameters(self.json_response_mode))
        return extract_message_content(response)


def extract_message_content(response):
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("watsonx Chat response did not contain model message content.") from exc

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        return "".join(text_parts)
    return str(content)
