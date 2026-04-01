"""Tests for the synthetic user test runner — happy path, error handling, and schema validation."""

import json
from unittest.mock import MagicMock, patch

import pytest

from propra.schemas.synthetic_test import (
    ComparisonResult,
    EvaluationResult,
    Persona,
)
from propra.eval.synthetic_user_test import (
    _fill_comparison,
    _fill_eval,
    _fill_response,
    _make_row,
    _parse_llm_json,
    generate_query,
    evaluate_response,
    compare_responses,
    call_assess,
    run,
    write_csv,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def persona():
    return Persona(role="Hauseigentümer", trait="ängstlicher Anfänger")


@pytest.fixture
def sample_assess_response():
    return {
        "verdict": "CONDITIONAL",
        "confidence": "MEDIUM",
        "explanation": "Ein Zaun bis 1,20 m ist in Brandenburg genehmigungsfrei.",
        "cited_sources": [
            {
                "paragraph": "§ 55 Abs. 9",
                "regulation_name": "Brandenburgische Bauordnung (BbgBO)",
                "jurisdiction": "Brandenburg",
                "excerpt": "Einfriedungen bis 1,20 m Höhe sind verfahrensfrei.",
            }
        ],
        "next_action": "Prüfen Sie die genaue Höhe Ihres geplanten Zauns.",
        "kg_status": "not_requested",
        "retrieval_mode": "rag",
        "has_bplan": False,
    }


@pytest.fixture
def sample_eval_json():
    return json.dumps({
        "task_success": "Yes",
        "user_confidence": 4,
        "trustworthiness": 4,
        "clarity": 5,
        "usability": 4,
        "traceability": 3,
        "key_issue": "Keine Probleme erkannt.",
    })


@pytest.fixture
def sample_comparison_json():
    return json.dumps({
        "trustworthiness_rag": 4,
        "trustworthiness_graphrag": 5,
        "clarity_rag": 4,
        "clarity_graphrag": 4,
        "usability_rag": 3,
        "usability_graphrag": 4,
        "preferred_version": "graphrag",
        "preference_reason": "Mehr Kontext durch Wissengraph.",
    })


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestEvaluationResultSchema:
    def test_valid(self):
        result = EvaluationResult(
            task_success="Yes", user_confidence=4, trustworthiness=4,
            clarity=5, usability=4, traceability=3, key_issue="Alles gut.",
        )
        assert result.clarity == 5

    def test_rejects_out_of_range_score(self):
        with pytest.raises(Exception):
            EvaluationResult(
                task_success="Yes", user_confidence=6, trustworthiness=4,
                clarity=5, usability=4, traceability=3, key_issue="Test",
            )

    def test_rejects_zero_score(self):
        with pytest.raises(Exception):
            EvaluationResult(
                task_success="Yes", user_confidence=0, trustworthiness=4,
                clarity=5, usability=4, traceability=3, key_issue="Test",
            )

    def test_rejects_invalid_success(self):
        with pytest.raises(Exception):
            EvaluationResult(
                task_success="Maybe", user_confidence=3, trustworthiness=4,
                clarity=5, usability=4, traceability=3, key_issue="Test",
            )


class TestComparisonResultSchema:
    def test_valid(self):
        result = ComparisonResult(
            trustworthiness_rag=4, trustworthiness_graphrag=5,
            clarity_rag=4, clarity_graphrag=4,
            usability_rag=3, usability_graphrag=4,
            preferred_version="graphrag", preference_reason="Better context.",
        )
        assert result.preferred_version == "graphrag"

    def test_rejects_invalid_preference(self):
        with pytest.raises(Exception):
            ComparisonResult(
                trustworthiness_rag=4, trustworthiness_graphrag=5,
                clarity_rag=4, clarity_graphrag=4,
                usability_rag=3, usability_graphrag=4,
                preferred_version="hybrid", preference_reason="Test",
            )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

class TestParseJson:
    def test_plain_json(self):
        result = _parse_llm_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_markdown_fenced_json(self):
        raw = '```json\n{"key": "value"}\n```'
        result = _parse_llm_json(raw)
        assert result == {"key": "value"}

    def test_markdown_no_lang(self):
        raw = '```\n{"key": "value"}\n```'
        result = _parse_llm_json(raw)
        assert result == {"key": "value"}


class TestHelperFunctions:
    def test_make_row(self, persona):
        row = _make_row(persona, "Zaun", "Darf ich?", "rag")
        assert row.persona_role == "Hauseigentümer"
        assert row.retrieval_mode == "rag"
        assert row.verdict is None

    def test_fill_response(self, persona, sample_assess_response):
        row = _make_row(persona, "Zaun", "Darf ich?", "rag")
        _fill_response(row, sample_assess_response, 1234)
        assert row.verdict == "CONDITIONAL"
        assert row.response_time_ms == 1234
        assert "§ 55" in row.cited_sources

    def test_fill_eval(self, persona):
        row = _make_row(persona, "Zaun", "Darf ich?", "rag")
        evaluation = EvaluationResult(
            task_success="Partial", user_confidence=3, trustworthiness=3,
            clarity=4, usability=3, traceability=2, key_issue="Fehlende Details.",
        )
        _fill_eval(row, evaluation)
        assert row.task_success == "Partial"
        assert row.usability == 3

    def test_fill_comparison(self, persona):
        row = _make_row(persona, "Zaun", "Darf ich?", "graphrag")
        comparison = ComparisonResult(
            trustworthiness_rag=3, trustworthiness_graphrag=4,
            clarity_rag=4, clarity_graphrag=4,
            usability_rag=3, usability_graphrag=5,
            preferred_version="graphrag", preference_reason="Besser.",
        )
        _fill_comparison(row, comparison)
        assert row.cmp_preferred_version == "graphrag"
        assert row.cmp_usability_graphrag == 5


# ---------------------------------------------------------------------------
# Core functions with mocked OpenAI + HTTP
# ---------------------------------------------------------------------------

class TestGenerateQuery:
    @patch("propra.eval.synthetic_user_test.OpenAI")
    def test_returns_string(self, mock_openai_cls, persona):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Darf ich einen Zaun bauen?"))]
        )
        result = generate_query(mock_client, persona, "Zaun", "Brandenburg")
        assert "Zaun" in result


class TestCallAssess:
    @patch("propra.eval.synthetic_user_test.httpx.post")
    def test_returns_response_and_time(self, mock_post, sample_assess_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_assess_response
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        data, ms = call_assess("Darf ich einen Zaun bauen?", "rag")
        assert data["verdict"] == "CONDITIONAL"
        assert isinstance(ms, int)
        assert ms >= 0


class TestEvaluateResponse:
    @patch("propra.eval.synthetic_user_test.OpenAI")
    def test_returns_validated_result(self, mock_openai_cls, persona, sample_assess_response, sample_eval_json):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=sample_eval_json))]
        )
        result = evaluate_response(mock_client, "Darf ich?", sample_assess_response, persona, "rag")
        assert isinstance(result, EvaluationResult)
        assert result.task_success == "Yes"
        assert result.usability == 4


class TestCompareResponses:
    @patch("propra.eval.synthetic_user_test.OpenAI")
    def test_returns_comparison(self, mock_openai_cls, persona, sample_assess_response, sample_comparison_json):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=sample_comparison_json))]
        )
        result = compare_responses(
            mock_client, "Darf ich?", sample_assess_response, sample_assess_response, persona,
        )
        assert isinstance(result, ComparisonResult)
        assert result.preferred_version == "graphrag"


# ---------------------------------------------------------------------------
# Full run (all external calls mocked)
# ---------------------------------------------------------------------------

class TestRun:
    @patch("propra.eval.synthetic_user_test.compare_responses")
    @patch("propra.eval.synthetic_user_test.evaluate_response")
    @patch("propra.eval.synthetic_user_test.call_assess")
    @patch("propra.eval.synthetic_user_test.generate_query")
    @patch("propra.eval.synthetic_user_test.OpenAI")
    def test_full_loop(
        self, mock_openai_cls, mock_gen, mock_assess, mock_eval, mock_cmp, persona, sample_assess_response,
    ):
        mock_gen.return_value = "Darf ich einen Zaun bauen?"
        mock_assess.return_value = (sample_assess_response, 500)
        mock_eval.return_value = EvaluationResult(
            task_success="Yes", user_confidence=4, trustworthiness=4,
            clarity=5, usability=4, traceability=3, key_issue="Keine Probleme erkannt.",
        )
        mock_cmp.return_value = ComparisonResult(
            trustworthiness_rag=4, trustworthiness_graphrag=5,
            clarity_rag=4, clarity_graphrag=4,
            usability_rag=3, usability_graphrag=4,
            preferred_version="graphrag", preference_reason="Mehr Kontext.",
        )

        results = run(
            personas=[persona],
            tasks=["Zaun um das Grundstück bauen — welche Regeln gelten in Brandenburg?"],
            delay=0,
            timeout=123,
        )

        # 1 persona × 1 task × 2 modes = 2 rows
        assert len(results) == 2
        assert results[0].retrieval_mode == "rag"
        assert results[1].retrieval_mode == "graphrag"
        assert results[1].cmp_preferred_version == "graphrag"
        assert mock_assess.call_count == 2
        assert all(call.kwargs["timeout"] == 123 for call in mock_assess.call_args_list)

    @patch("propra.eval.synthetic_user_test.compare_responses")
    @patch("propra.eval.synthetic_user_test.evaluate_response")
    @patch("propra.eval.synthetic_user_test.call_assess")
    @patch("propra.eval.synthetic_user_test.generate_query")
    @patch("propra.eval.synthetic_user_test.OpenAI")
    def test_streams_rows_to_csv_during_run(
        self, mock_openai_cls, mock_gen, mock_assess, mock_eval, mock_cmp, tmp_path, persona, sample_assess_response,
    ):
        mock_gen.return_value = "Darf ich einen Zaun bauen?"
        mock_assess.return_value = (sample_assess_response, 500)
        mock_eval.return_value = EvaluationResult(
            task_success="Yes", user_confidence=4, trustworthiness=4,
            clarity=5, usability=4, traceability=3, key_issue="Keine Probleme erkannt.",
        )
        mock_cmp.return_value = ComparisonResult(
            trustworthiness_rag=4, trustworthiness_graphrag=5,
            clarity_rag=4, clarity_graphrag=4,
            usability_rag=3, usability_graphrag=4,
            preferred_version="graphrag", preference_reason="Mehr Kontext.",
        )

        output = tmp_path / "stream.csv"
        results = run(
            personas=[persona],
            tasks=["Zaun um das Grundstück bauen — welche Regeln gelten in Brandenburg?"],
            delay=0,
            output_path=output,
        )

        assert len(results) == 2
        assert output.exists()
        with open(output, encoding="utf-8", newline="") as f:
            reader = list(csv.DictReader(f))
        assert len(reader) == 2
        assert reader[0]["retrieval_mode"] == "rag"
        assert reader[1]["retrieval_mode"] == "graphrag"

    @patch("propra.eval.synthetic_user_test.evaluate_response")
    @patch("propra.eval.synthetic_user_test.call_assess")
    @patch("propra.eval.synthetic_user_test.generate_query")
    @patch("propra.eval.synthetic_user_test.OpenAI")
    def test_handles_assess_error_gracefully(
        self, mock_openai_cls, mock_gen, mock_assess, mock_eval, persona,
    ):
        mock_gen.return_value = "Darf ich einen Zaun bauen?"
        mock_assess.side_effect = Exception("503 Service Unavailable")

        results = run(
            personas=[persona],
            tasks=["Zaun um das Grundstück bauen — welche Regeln gelten in Brandenburg?"],
            delay=0,
            timeout=77,
        )

        assert len(results) == 2
        assert all(r.error is not None for r in results)
        assert all(call.kwargs["timeout"] == 77 for call in mock_assess.call_args_list)


class TestWriteCsv:
    def test_writes_valid_csv(self, tmp_path, persona):
        row = _make_row(persona, "Zaun", "Darf ich?", "rag")
        row.verdict = "ALLOWED"
        row.response_time_ms = 200

        output = tmp_path / "test.csv"
        write_csv([row], output)

        assert output.exists()
        with open(output, encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["verdict"] == "ALLOWED"
        assert reader[0]["response_time_ms"] == "200"


import csv  # noqa: E402 — needed for TestWriteCsv
