"""Deterministic eligibility rules based only on extracted evidence."""

from __future__ import annotations

from .models import CandidateProfile, EligibilityDecision, EligibilityStatus


def evaluate_eligibility(candidate: CandidateProfile) -> EligibilityDecision:
    """Require concrete Python and meaningful AI/LLM implementation evidence.

    This intentionally never consults an LLM: eligibility must be repeatable and
    explainable from facts captured during extraction.
    """
    reasons: list[str] = []
    if not candidate.python_evidence:
        reasons.append("No demonstrated Python skill, project technology, or implementation evidence.")
    if not candidate.ai_evidence:
        reasons.append(
            "No meaningful AI/LLM/RAG/agentic project, framework, or implementation evidence."
        )

    return EligibilityDecision(
        status=EligibilityStatus.ELIGIBLE if not reasons else EligibilityStatus.REJECTED,
        reasons=reasons,
    )

