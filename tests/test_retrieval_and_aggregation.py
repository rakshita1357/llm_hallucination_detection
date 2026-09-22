import os
import json
import builtins
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app and modules
from main import app
from Backend.modules.retrieval import retrieve_for_claims
from Backend.modules.aggregation import aggregate_claims

# Helper to mock Exa API responses
class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
    def json(self):
        return self._json
    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")

@pytest.fixture(autouse=True)
def set_dummy_exa_key(monkeypatch):
    # Ensure EXA_API_KEY is set for the duration of the test
    monkeypatch.setenv("EXA_API_KEY", "dummy-key")
    # Unset API keys to force fallback paths
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    yield

def test_exa_retrieval_mock(monkeypatch):
    # Mock requests.post used inside retrieval._search
    def mock_post(url, json, headers, timeout):
        assert url == "https://api.exa.ai/search"
        # Return a deterministic result for any query
        return DummyResponse({
            "results": [
                {
                    "title": "Example Title",
                    "url": "https://example.com",
                    "contents": {"highlights": "Example snippet containing answer."}
                }
            ]
        })
    monkeypatch.setattr("requests.post", mock_post)

    claim = {
        "id": "c1",
        "text": "Test claim",
        "self_confidence": 0.4,
        "needs_retrieval": True,
        "search_query": "test query",
    }
    enriched = retrieve_for_claims([claim])
    assert enriched[0]["evidence"]  # evidence list should not be empty
    ev = enriched[0]["evidence"][0]
    assert ev["snippet"] == "Example snippet containing answer."
    assert ev["source"] == "https://example.com"
    assert ev["title"] == "Example Title"

def test_aggregation_uses_self_confidence():
    claims = [
        {
            "id": "c1",
            "text": "A simple true claim.",
            "verdict": "insufficient_evidence",
            "self_confidence": 0.9,
            "needs_retrieval": False,
        }
    ]
    result = aggregate_claims(claims)
    # With new evidence-weighted aggregation:
    # - insufficient_evidence base score is 0.1 (not 0.5)
    # - self_confidence boost contributes: 0.2 * (0.9 * 0.3) = 0.054
    # - evidence quality is 0 (no evidence)
    # - Total: 0.6*0.1 + 0.2*0 + 0.2*0.27 = 0.06 + 0.054 = 0.114
    # This is CORRECT: without evidence, confidence should be LOW regardless of self-confidence
    assert result["aggregate_confidence"] == pytest.approx(0.114, rel=1e-2)
    assert result["report"][0]["score"] == pytest.approx(0.114, rel=1e-2)

def test_chat_endpoint_integration(monkeypatch):
    client = TestClient(app)

    # Mock Exa search (same as above)
    def mock_exa_post(url, json, headers, timeout):
        return DummyResponse({
            "results": [
                {
                    "title": "France Capital",
                    "url": "https://en.wikipedia.org/wiki/Paris",
                    "contents": {"highlights": "Paris is the capital of France."}
                }
            ]
        })
    monkeypatch.setattr("requests.post", mock_exa_post)

    # Mock OpenRouter call_model to always return a supported verdict
    def mock_call_model(model_id, system_prompt, user_prompt):
        # Build a minimal JSON response with a supported verdict for claim c1
        return json.dumps({"verdicts": [{"id": "c1", "verdict": "supported"}]})
    monkeypatch.setattr("Backend.modules.openrouter_verification.call_model", mock_call_model)
    monkeypatch.setattr("Backend.modules.openrouter_client.call_model", mock_call_model)

    # Perform a chat request for a known capital question
    response = client.post("/api/chat", json={"prompt": "What is the capital of France?", "model": "gemini-3-1-pro", "attachments": [], "history": []})
    assert response.status_code == 200
    payload = response.json()
    print("PAYLOAD:", payload)
    # Answer should contain Paris
    assert "Paris" in payload["answer"]
    # Confidence should be high (>=0.85) and status verified
    assert payload["confidence"] >= 0.85
    assert payload["status"] == "verified"
    # No findings for a fully supported claim
    assert payload["findings"] == []
