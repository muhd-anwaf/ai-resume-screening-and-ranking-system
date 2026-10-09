"""Transparent, capped scoring based on explicit evidence."""

from __future__ import annotations

from .config import ScoringWeights
from .models import CandidateProfile, GitHubSummary, ScoreBreakdown


def _cap(value: float, maximum: int) -> float:
    return round(min(max(value, 0), maximum), 2)


def score_candidate(candidate: CandidateProfile, github: GitHubSummary, weights: ScoringWeights) -> ScoreBreakdown:
    """Score facts, not mere keyword counts; every section is independently capped."""
    implementation_count = sum(len(project.implementation_evidence) for project in candidate.projects)
    ai_score = _cap(12 + min(len(candidate.ai_evidence), 4) * 5 + min(implementation_count, 3) * 3, weights.ai_project_depth) if candidate.ai_evidence else 0
    python_score = _cap(min(len(candidate.python_evidence), 4) * 5 + min(len(candidate.backend_evidence), 3) * 3 + 1, weights.python_backend) if candidate.python_evidence else 0
    cloud_score = _cap(min(len(candidate.cloud_evidence), 3) * 4 + (3 if "react" in candidate.skills or "next.js" in candidate.skills else 0), weights.cloud_full_stack)
    github_score = 0.0
    if github.status == "enriched":
        github_score += min((github.recent_push_events or 0), 5)
        github_score += min(len(github.relevant_repositories) * 2, 5)
    engineering_score = _cap(min(len(candidate.backend_evidence), 2) * 2 + (1 if candidate.projects else 0), weights.engineering_depth)
    deductions: list[str] = []
    evidence_text = " ".join(project.summary.lower() for project in candidate.projects)
    if candidate.ai_evidence and not any(term in evidence_text for term in ("retriev", "embed", "vector", "tool", "agent", "evaluat", "pipeline")):
        ai_score = _cap(ai_score - 8, weights.ai_project_depth)
        deductions.append("Reduced AI score: evidence does not describe implementation depth beyond an LLM/API claim.")
    return ScoreBreakdown(ai_project_depth=ai_score, python_backend=python_score, cloud_full_stack=cloud_score, github_activity=_cap(github_score, weights.github_activity), engineering_depth=engineering_score, deductions=deductions)
