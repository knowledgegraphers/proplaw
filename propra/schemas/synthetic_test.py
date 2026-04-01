"""Pydantic models for synthetic user testing — personas, test cases, and evaluation results.

Aligned with the PropLaw User Testing Protocol v2.0: three tasks, dual retrieval
modes (RAG + GraphRAG), observation-sheet scoring dimensions, and RAG/GraphRAG
comparison metrics.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """A synthetic user persona for testing."""

    role: str = Field(..., description="Role of the persona, e.g. 'homeowner', 'legal advisor'.")
    trait: str = Field(..., description="Key personality trait, e.g. 'anxious beginner'.")
    description: str = Field(
        default="",
        description="Optional longer description of the persona for context.",
    )


class EvaluationResult(BaseModel):
    """Structured evaluation of a single response — mirrors the observation sheet."""

    task_success: Literal["Yes", "Partial", "No"] = Field(
        ..., description="Whether the response answered the persona's question."
    )
    user_confidence: int = Field(
        ..., ge=1, le=5,
        description="How much the persona would trust and act on this answer (1–5).",
    )
    trustworthiness: int = Field(
        ..., ge=1, le=5, description="Does the answer appear credible and correct? (1–5)"
    )
    clarity: int = Field(
        ..., ge=1, le=5, description="How clear is the explanation for this persona? (1–5)"
    )
    usability: int = Field(
        ..., ge=1, le=5, description="Is the next action concrete and actionable? (1–5)"
    )
    traceability: int = Field(
        ..., ge=1, le=5, description="Can claims be traced to cited sources? (1–5)"
    )
    key_issue: str = Field(
        ..., max_length=200,
        description="One-sentence summary of the main issue, or 'Keine Probleme erkannt.'",
    )


class ComparisonResult(BaseModel):
    """RAG vs GraphRAG comparison — mirrors the observation sheet comparison section."""

    trustworthiness_rag: int = Field(..., ge=1, le=5)
    trustworthiness_graphrag: int = Field(..., ge=1, le=5)
    clarity_rag: int = Field(..., ge=1, le=5)
    clarity_graphrag: int = Field(..., ge=1, le=5)
    usability_rag: int = Field(..., ge=1, le=5)
    usability_graphrag: int = Field(..., ge=1, le=5)
    preferred_version: Literal["rag", "graphrag"] = Field(
        ..., description="Which version the persona would prefer.",
    )
    preference_reason: str = Field(
        ..., max_length=300, description="Short reason for the preference.",
    )


class SyntheticTestRow(BaseModel):
    """One row in the output CSV — one persona × task × mode combination."""

    persona_role: str
    persona_trait: str
    task: str
    generated_query: str
    retrieval_mode: str
    # Response fields
    verdict: str | None = None
    confidence: str | None = None
    explanation: str | None = None
    cited_sources: str | None = None
    next_action: str | None = None
    kg_status: str | None = None
    response_time_ms: int | None = None
    # Evaluation fields (per-mode)
    task_success: str | None = None
    user_confidence: int | None = None
    trustworthiness: int | None = None
    clarity: int | None = None
    usability: int | None = None
    traceability: int | None = None
    key_issue: str | None = None
    # Comparison fields (filled only on graphrag row after both modes run)
    cmp_trustworthiness_rag: int | None = None
    cmp_trustworthiness_graphrag: int | None = None
    cmp_clarity_rag: int | None = None
    cmp_clarity_graphrag: int | None = None
    cmp_usability_rag: int | None = None
    cmp_usability_graphrag: int | None = None
    cmp_preferred_version: str | None = None
    cmp_preference_reason: str | None = None
    error: str | None = None
