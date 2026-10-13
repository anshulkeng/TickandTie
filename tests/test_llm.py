"""Unit tests for the model switch. The hosted API is faked; no network call is made."""
import io
import json

import pytest

from tickandtie import llm

MESSAGES = [{"role": "user", "content": "hi"}]


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_local_ollama_is_the_default(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    assert llm.backend() == "ollama"


def test_the_hosted_model_needs_a_key(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(llm.ModelUnavailable, match="OPENROUTER_API_KEY"):
        llm.chat(MESSAGES)


def test_the_hosted_request_is_deterministic_and_asks_for_the_schema(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["body"] = json.loads(request.data.decode("utf-8"))
        seen["auth"] = request.get_header("Authorization")
        return FakeResponse(json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode("utf-8"))

    monkeypatch.setenv("LLM_BACKEND", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    assert llm.chat(MESSAGES, schema={"type": "object"}) == "ok"
    assert seen["auth"] == "Bearer test-key" and seen["body"]["temperature"] == 0
    assert seen["body"]["response_format"]["type"] == "json_schema"


def test_a_failed_hosted_call_is_reported_not_hidden(monkeypatch):
    def refused(request, timeout):
        raise llm.urllib.error.HTTPError(llm.OPENROUTER_URL, 402, "Payment Required", {}, None)

    monkeypatch.setenv("LLM_BACKEND", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(llm.urllib.request, "urlopen", refused)
    with pytest.raises(llm.ModelUnavailable, match="402"):
        llm.chat(MESSAGES)

def test_the_router_calls_the_model_through_the_switch(monkeypatch):
    # Found while wiring: a half-applied edit made routing fail silently, and no test called the real function.
    # The fake answers Item 7A, which the real model would not pick for a risk question, so this cannot pass by accident.
    from tickandtie.agents.router import ask_model
    monkeypatch.setattr(llm, "chat", lambda messages, schema=None, num_ctx=None:
                        '{"needs_text": true, "sections": ["Item 7A"]}')
    decision, error = ask_model("What risks does Pfizer describe?")
    assert error is None and decision.sections == ["Item 7A"]


def test_the_writer_calls_the_model_through_the_switch(monkeypatch):
    from tickandtie.agents.writer import ollama_chat
    monkeypatch.setattr(llm, "chat", lambda messages, schema=None, num_ctx=None: "Answer [F1].")
    assert ollama_chat([{"role": "user", "content": "q"}]) == "Answer [F1]."

def test_a_slow_hosted_call_times_out_and_counts_as_unavailable(monkeypatch):
    seen = {}

    def slow(request, timeout):
        seen["timeout"] = timeout
        raise TimeoutError("timed out")

    monkeypatch.setenv("LLM_BACKEND", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TICKANDTIE_LLM_TIMEOUT", "40")
    monkeypatch.setattr(llm.urllib.request, "urlopen", slow)
    with pytest.raises(llm.ModelUnavailable, match="timed out"):
        llm.chat(MESSAGES)
    assert seen["timeout"] == 40.0