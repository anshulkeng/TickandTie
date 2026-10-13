"""One place to call the language model: local Ollama (the default) or hosted on OpenRouter (decision 0019).

Set LLM_BACKEND=openrouter and OPENROUTER_API_KEY to use the hosted model. A failed hosted call raises
ModelUnavailable, so callers can fall back to demo mode instead of failing silently."""
import json
import os
import urllib.error
import urllib.request

from tickandtie import config

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_HOSTED_MODEL = "qwen/qwen-2.5-7b-instruct"
TIMEOUT_SECONDS = 40  # per model call; change with TICKANDTIE_LLM_TIMEOUT


class ModelUnavailable(RuntimeError):
    """The hosted model could not answer, for example because the spending limit was reached."""


def timeout_seconds():
    return float(os.environ.get("TICKANDTIE_LLM_TIMEOUT", TIMEOUT_SECONDS))


def backend():
    return os.environ.get("LLM_BACKEND", "ollama").strip().lower()


def chat(messages, schema=None, num_ctx=None):
    """The model's reply text. schema asks for JSON in that shape; num_ctx sets Ollama's context window."""
    if backend() == "openrouter":
        return openrouter_chat(messages, schema)
    import ollama
    options = {"temperature": 0, "seed": 7}
    if num_ctx:
        options["num_ctx"] = num_ctx
    response = ollama.chat(model=config.LLM_MODEL, messages=messages, format=schema, options=options)
    return response["message"]["content"]


def openrouter_chat(messages, schema=None):
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ModelUnavailable("OPENROUTER_API_KEY is not set")
    body = {"model": os.environ.get("OPENROUTER_MODEL", DEFAULT_HOSTED_MODEL),
            "messages": messages, "temperature": 0, "seed": 7}
    if schema:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "reply", "strict": False, "schema": schema}}
    request = urllib.request.Request(OPENROUTER_URL, data=json.dumps(body).encode("utf-8"),
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds()) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ModelUnavailable(f"hosted model returned HTTP {exc.code}") from exc
    except TimeoutError as exc:
        raise ModelUnavailable("hosted model timed out") from exc
    except urllib.error.URLError as exc:
        raise ModelUnavailable(f"hosted model unreachable: {exc.reason}") from exc
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelUnavailable(f"unexpected reply from the hosted model: {str(data)[:200]}") from exc