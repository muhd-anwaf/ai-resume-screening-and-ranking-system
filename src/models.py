"""Validated domain models for resume evidence and pipeline output."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    REJECTED = "rejected"
    PROCESSING_FAILED = "processing_failed"


class EvidenceItem(BaseModel):
    label: str
    excerpt: str
    source: str = "resume"


class GitHubUrlEvidence(BaseModel):
    """A GitHub-like URL and how it was discovered in the resume."""

    raw_url: str
    normalized_url: str | None = None
    source: str  # ``visible_text`` or ``pdf_hyperlink``
    username: str | None = None
    is_profile_candidate: bool = False
    detail: str | None = None


class ProjectEvidence(BaseModel):
    name: str
    summary: str = ""
    technologies: list[str] = Field(default_factory=list)
    implementation_evidence: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    source_file: str
    name: str | None = None
    email: str | None = None
    github_username: str | None = None
    github_profile_url: str | None = None
    github_url_evidence: list[GitHubUrlEvidence] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    python_evidence: list[EvidenceItem] = Field(default_factory=list)
    ai_evidence: list[EvidenceItem] = Field(default_factory=list)
    projects: list[ProjectEvidence] = Field(default_factory=list)
    cloud_evidence: list[EvidenceItem] = Field(default_factory=list)
    backend_evidence: list[EvidenceItem] = Field(default_factory=list)
    extraction_errors: list[str] = Field(default_factory=list)


class EligibilityDecision(BaseModel):
    status: EligibilityStatus
    reasons: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    ai_project_depth: float = Field(default=0, ge=0, le=40)
    python_backend: float = Field(default=0, ge=0, le=30)
    cloud_full_stack: float = Field(default=0, ge=0, le=15)
    github_activity: float = Field(default=0, ge=0, le=10)
    engineering_depth: float = Field(default=0, ge=0, le=5)
    deductions: list[str] = Field(default_factory=list)

    @property
    def total(self) -> float:
        return round(
            self.ai_project_depth
            + self.python_backend
            + self.cloud_full_stack
            + self.github_activity
            + self.engineering_depth,
            2,
        )


class GitHubSummary(BaseModel):
    status: str
    username: str | None = None
    public_repos: int | None = None
    recent_push_events: int | None = None
    relevant_repositories: list[str] = Field(default_factory=list)
    message: str | None = None


class CandidateResult(BaseModel):
    rank: int | None = None
    source_file: str
    name: str | None = None
    email: str | None = None
    eligibility: EligibilityDecision
    total_score: float | None = None
    score_components: ScoreBreakdown | None = None
    matched_skills: list[str] = Field(default_factory=list)
    project_summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    github: GitHubSummary
    errors: list[str] = Field(default_factory=list)


class BatchSummary(BaseModel):
    total_resumes: int
    successfully_parsed: int
    eligible_candidates: int
    rejected_candidates: int
    failed_unreadable_resumes: int


class BatchReport(BaseModel):
    summary: BatchSummary
    candidates: list[CandidateResult]
