"""Replaceable extension point for optional semantic resume analysis."""

from __future__ import annotations

from typing import Protocol

from .models import CandidateProfile


class ResumeAnalysisAdapter(Protocol):
    def enrich(self, candidate: CandidateProfile, resume_text: str) -> CandidateProfile:
        """Return validated additions only; callers retain deterministic eligibility."""


class DisabledLLMAdapter:
    """Safe default when no provider or API key is configured."""

    def enrich(self, candidate: CandidateProfile, resume_text: str) -> CandidateProfile:
        return candidate
