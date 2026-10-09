"""Batch orchestration: an error in one resume never stops the batch."""

from __future__ import annotations

from pathlib import Path

from .config import Settings
from .eligibility import evaluate_eligibility
from .extractor import extract_candidate
from .github_client import GitHubClient
from .llm_adapter import DisabledLLMAdapter, ResumeAnalysisAdapter
from .models import BatchReport, BatchSummary, CandidateResult, EligibilityDecision, EligibilityStatus, GitHubSummary
from .parser import ResumeParseError, parse_pdf
from .scorer import score_candidate


def _summary(candidate) -> str:
    if not candidate.projects:
        return "No project implementation evidence extracted."
    return " ".join(project.summary for project in candidate.projects[:2])[:900]


def run_pipeline(input_dir: Path, settings: Settings, llm: ResumeAnalysisAdapter | None = None) -> BatchReport:
    adapter = llm or DisabledLLMAdapter()
    github_client = GitHubClient(settings.github_token)
    files = sorted(path for path in input_dir.glob("*.pdf") if path.is_file())
    results: list[CandidateResult] = []
    parsed = 0
    for path in files:
        try:
            parsed_resume = parse_pdf(path)
            text = parsed_resume.text
            parsed += 1
            candidate = extract_candidate(text, path.name, parsed_resume.hyperlink_uris)
            try:
                candidate = adapter.enrich(candidate, text)
            except Exception as exc:
                # Semantic enrichment is optional. Preserve deterministic facts.
                candidate.extraction_errors.append(f"LLM enrichment unavailable; used deterministic extraction: {exc}")
            decision = evaluate_eligibility(candidate)
            github = github_client.enrich(candidate.github_username)
            if decision.status is EligibilityStatus.ELIGIBLE:
                score = score_candidate(candidate, github, settings.scoring)
                strengths = [item.excerpt for item in (candidate.ai_evidence + candidate.python_evidence)[:3]]
                concerns = list(score.deductions)
                results.append(CandidateResult(source_file=path.name, name=candidate.name, email=candidate.email, eligibility=decision, total_score=score.total, score_components=score, matched_skills=candidate.skills, project_summary=_summary(candidate), strengths=strengths, concerns=concerns, github=github, errors=candidate.extraction_errors))
            else:
                results.append(CandidateResult(source_file=path.name, name=candidate.name, email=candidate.email, eligibility=decision, matched_skills=candidate.skills, project_summary=_summary(candidate), concerns=decision.reasons, github=github, errors=candidate.extraction_errors))
        except (ResumeParseError, Exception) as exc:
            # Unexpected per-file failures are preserved as report data, never propagated.
            results.append(CandidateResult(source_file=path.name, eligibility=EligibilityDecision(status=EligibilityStatus.PROCESSING_FAILED, reasons=["Resume could not be processed."]), github=GitHubSummary(status="not_attempted"), errors=[str(exc)]))
    eligible = sorted((result for result in results if result.eligibility.status is EligibilityStatus.ELIGIBLE), key=lambda result: result.total_score or 0, reverse=True)
    for index, result in enumerate(eligible, start=1):
        result.rank = index
    failed = sum(result.eligibility.status is EligibilityStatus.PROCESSING_FAILED for result in results)
    return BatchReport(summary=BatchSummary(total_resumes=len(files), successfully_parsed=parsed, eligible_candidates=len(eligible), rejected_candidates=sum(result.eligibility.status is EligibilityStatus.REJECTED for result in results), failed_unreadable_resumes=failed), candidates=results)
