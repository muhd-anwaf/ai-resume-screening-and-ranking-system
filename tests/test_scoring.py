from src.config import ScoringWeights
from src.models import CandidateProfile, EvidenceItem, GitHubSummary, ProjectEvidence
from src.scorer import score_candidate


def test_scores_are_capped_at_configured_maximums() -> None:
    candidate = CandidateProfile(
        source_file="a.pdf",
        python_evidence=[EvidenceItem(label="Python", excerpt="Python service")] * 12,
        ai_evidence=[EvidenceItem(label="RAG", excerpt="RAG implementation")] * 12,
        backend_evidence=[EvidenceItem(label="API", excerpt="FastAPI")] * 12,
        cloud_evidence=[EvidenceItem(label="Cloud", excerpt="AWS deployment")] * 12,
        projects=[ProjectEvidence(name="RAG", summary="retrieval embeddings vector tool agent pipeline", implementation_evidence=["built"] * 8)],
    )
    github = GitHubSummary(status="enriched", recent_push_events=30, relevant_repositories=["a"] * 8)

    score = score_candidate(candidate, github, ScoringWeights())

    assert score.total <= 100
    assert score.ai_project_depth <= 40
    assert score.python_backend <= 30
    assert score.github_activity <= 10


def test_missing_github_profile_does_not_reduce_other_scores() -> None:
    candidate = CandidateProfile(source_file="a.pdf", python_evidence=[EvidenceItem(label="Python", excerpt="Python")], ai_evidence=[EvidenceItem(label="RAG", excerpt="RAG vector pipeline")], projects=[ProjectEvidence(name="RAG", summary="vector pipeline", implementation_evidence=["built"])])
    score = score_candidate(candidate, GitHubSummary(status="not_provided"), ScoringWeights())
    assert score.github_activity == 0
    assert score.python_backend > 0
    assert score.ai_project_depth > 0
