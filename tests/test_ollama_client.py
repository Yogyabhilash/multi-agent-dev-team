
import httpx
import pytest

from api.agents.ollama_client import OllamaClient


def test_generate_returns_model_response(monkeypatch):
    def fake_post(url, json, timeout):
        assert url == "http://localhost:11434/api/generate"
        assert json["model"] == "qwen2.5:3b"
        assert json["stream"] is False

        return httpx.Response(
            200,
            json={"response": "Step 1: Plan the website."},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    client = OllamaClient()
    result = client.generate("Plan a website")

    assert result == "Step 1: Plan the website."


def test_generate_rejects_empty_prompt():
    client = OllamaClient()

    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        client.generate("   ")


def test_generate_rejects_empty_model_response(monkeypatch):
    def fake_post(url, json, timeout):
        return httpx.Response(
            200,
            json={"response": "   "},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    client = OllamaClient()

    with pytest.raises(RuntimeError, match="empty response"):
        client.generate("Plan a website")
