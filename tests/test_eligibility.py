from src.eligibility import evaluate_eligibility
from src.models import CandidateProfile, EligibilityStatus, EvidenceItem


def candidate(**overrides: object) -> CandidateProfile:
    return CandidateProfile(source_file="resume.pdf", **overrides)


def test_candidate_with_python_and_meaningful_ai_evidence_is_eligible() -> None:
    profile = candidate(
        python_evidence=[EvidenceItem(label="Python", excerpt="Built the service in Python.")],
        ai_evidence=[
            EvidenceItem(
                label="RAG pipeline",
                excerpt="Implemented retrieval, embeddings, vector search, and source citations.",
            )
        ],
    )

    assert evaluate_eligibility(profile).status is EligibilityStatus.ELIGIBLE


def test_javascript_and_java_only_candidate_is_rejected() -> None:
    profile = candidate(
        skills=["JavaScript", "React", "Java"],
        ai_evidence=[EvidenceItem(label="LangChain", excerpt="Used LangChain in a JavaScript application.")],
    )

    decision = evaluate_eligibility(profile)

    assert decision.status is EligibilityStatus.REJECTED
    assert any("Python" in reason for reason in decision.reasons)


def test_python_without_meaningful_ai_evidence_is_rejected() -> None:
    profile = candidate(
        python_evidence=[EvidenceItem(label="Python", excerpt="Used Python for data processing.")]
    )

    decision = evaluate_eligibility(profile)

    assert decision.status is EligibilityStatus.REJECTED
    assert any("AI/LLM/RAG" in reason for reason in decision.reasons)


def test_missing_both_requirements_reports_both_reasons() -> None:
    decision = evaluate_eligibility(candidate())

    assert decision.status is EligibilityStatus.REJECTED
    assert len(decision.reasons) == 2

