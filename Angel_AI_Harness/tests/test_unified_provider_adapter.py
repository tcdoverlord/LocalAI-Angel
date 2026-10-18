from __future__ import annotations
import json
from unittest.mock import patch
from angel_platform.webui import server

class FakeResponse:
    def __init__(self, lines, status=200): self.lines = lines; self.status = status
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.lines if isinstance(self.lines, bytes) else b""
    def __iter__(self):
        if isinstance(self.lines, list):
            for x in self.lines: yield x if isinstance(x, bytes) else str(x).encode()


def test_localai_models_are_discovered_from_openai_endpoint():
    body = json.dumps({"data": [{"id": "small-chat-q4", "object": "model"}]}).encode()
    with patch.object(server, "_json_get", return_value=json.loads(body)):
        assert server._localai_models()[0]["id"] == "small-chat-q4"


def test_openai_stream_delta_is_extracted():
    assert server._openai_piece({"choices": [{"delta": {"content": "Hello"}}]}) == "Hello"


def test_localai_is_default_provider(monkeypatch):
    monkeypatch.setattr(server, "CONFIGURED_PROVIDER", "localai")
    monkeypatch.setattr(server, "OLLAMA_FALLBACK_ENABLED", False)
    monkeypatch.setattr(server, "_localai_models", lambda: [{"id": "test-model", "object": "model"}])
    provider, models = server.active_provider_models(refresh=True)
    assert provider == "localai"
    assert [item["id"] for item in models] == ["test-model"]


def test_model_selection_uses_first_installed_model(monkeypatch):
    monkeypatch.setattr(server, "DEFAULT_MODEL", "")
    monkeypatch.setattr(server, "active_provider_models", lambda refresh=False: ("localai", [{"id":"first-model"},{"id":"second-model"}]))
    assert server._chosen_model("missing-model") == "first-model"
