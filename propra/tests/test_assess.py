"""Tests for the POST /assess endpoint — covers happy path and error path scenarios."""

from unittest.mock import MagicMock, patch

import anthropic
import pytest
from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────────

_SAMPLE_CHUNKS = [
    {
        "chunk_id": "DE-BB_§_6_0",
        "jurisdiction": "DE-BB",
        "jurisdiction_label": "Brandenburg",
        "source_file": "BbgBO",
        "source_paragraph": "§ 6",
        "text": "Garagen bis 50 m² Grundfläche sind zulässig, sofern die Abstandsflächen eingehalten werden.",
        "score": 0.82,
    }
]

_VALID_LLM_JSON = (
    '{"verdict": "CONDITIONAL", "confidence": "MEDIUM",'
    ' "explanation": "Eine Garage bis 50 m² ist in Brandenburg grundsätzlich zulässig.",'
    ' "cited_sources": [{"paragraph": "§ 6", "regulation_name": "BbgBO", "jurisdiction": "Brandenburg"}],'
    ' "next_action": "Prüfen Sie die Abstandsflächen und stellen Sie ggf. einen Bauantrag."}'
)


def _make_llm_response(text: str) -> MagicMock:
    """Build a mock Anthropic Messages response containing text."""
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


# ── happy path ────────────────────────────────────────────────────────────────


def test_assess_happy_path(client: TestClient, valid_situation: dict) -> None:
    """Valid situation returns 200 with a structured AssessmentResponse."""
    mock_llm = MagicMock(spec=anthropic.Anthropic)
    mock_llm.messages.create.return_value = _make_llm_response(_VALID_LLM_JSON)

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        response = client.post("/api/assess", json=valid_situation)

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] in {"ALLOWED", "CONDITIONAL", "NOT_ALLOWED"}
    assert body["confidence"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(body["explanation"], str) and len(body["explanation"]) > 0
    assert isinstance(body["cited_sources"], list)
    assert isinstance(body["next_action"], str) and len(body["next_action"]) > 0
    assert "has_bplan" in body


def test_assess_confidence_capped_without_bplan(client: TestClient, valid_situation: dict) -> None:
    """Confidence is downgraded from HIGH to MEDIUM when has_bplan is False."""
    high_conf_json = _VALID_LLM_JSON.replace('"MEDIUM"', '"HIGH"')
    mock_llm = MagicMock(spec=anthropic.Anthropic)
    mock_llm.messages.create.return_value = _make_llm_response(high_conf_json)

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        response = client.post("/api/assess", json={**valid_situation, "has_bplan": False})

    assert response.status_code == 200
    assert response.json()["confidence"] != "HIGH"


def test_assess_no_chunks_returns_low_confidence(client: TestClient, valid_situation: dict) -> None:
    """When the retriever finds no relevant chunks, the endpoint returns LOW confidence."""
    with patch("propra.api.assess._retriever") as mock_retriever:
        mock_retriever.retrieve.return_value = []
        response = client.post("/api/assess", json=valid_situation)

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "LOW"
    assert body["cited_sources"] == []


# ── error paths ───────────────────────────────────────────────────────────────


def test_assess_missing_required_field(client: TestClient, valid_situation: dict) -> None:
    """Request missing a required field returns 422 before reaching the assess logic."""
    incomplete = {k: v for k, v in valid_situation.items() if k != "has_bplan"}

    response = client.post("/api/assess", json=incomplete)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"][-1] == "has_bplan" for e in errors)


def test_assess_project_description_too_short(client: TestClient, valid_situation: dict) -> None:
    """project_description shorter than 10 characters returns 422."""
    payload = {**valid_situation, "project_description": "Kurz"}

    response = client.post("/api/assess", json=payload)

    assert response.status_code == 422


def test_assess_index_not_found_returns_503(client: TestClient, valid_situation: dict) -> None:
    """FileNotFoundError from retriever (index not built) returns 503."""
    with patch("propra.api.assess._retriever") as mock_retriever:
        mock_retriever.retrieve.side_effect = FileNotFoundError("FAISS index not found")
        response = client.post("/api/assess", json=valid_situation)

    assert response.status_code == 503
    body = response.json()
    assert "detail" in body
    assert "user_message" in body["detail"]


def test_assess_llm_error_returns_502(client: TestClient, valid_situation: dict) -> None:
    """Anthropic API error returns 502 with user_message."""
    mock_llm = MagicMock(spec=anthropic.Anthropic)
    mock_llm.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        response = client.post("/api/assess", json=valid_situation)

    assert response.status_code == 502
    assert "user_message" in response.json()["detail"]


def test_assess_extra_fields_ignored(client: TestClient, valid_situation: dict) -> None:
    """Extra fields sent by the frontend are silently ignored (extra='ignore')."""
    payload = {
        **valid_situation,
        "language": "de",
        "floors": 1,
        "inside_outside": "outside",
        "postcode": "14467",
    }
    mock_llm = MagicMock(spec=anthropic.Anthropic)
    mock_llm.messages.create.return_value = _make_llm_response(_VALID_LLM_JSON)

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        response = client.post("/api/assess", json=payload)

    assert response.status_code == 200
