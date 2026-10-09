from pathlib import Path

from src.config import load_settings
from src.parser import ParsedResume
from src.pipeline import run_pipeline


class FailingLLM:
    def enrich(self, candidate, resume_text):
        raise RuntimeError("provider unavailable")


def test_one_bad_resume_does_not_stop_batch(tmp_path: Path) -> None:
    (tmp_path / "bad.pdf").write_text("not a PDF", encoding="utf-8")
    report = run_pipeline(tmp_path, load_settings())
    assert report.summary.total_resumes == 1
    assert report.summary.failed_unreadable_resumes == 1
    assert len(report.candidates) == 1


def test_llm_failure_falls_back_to_deterministic_extraction(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "candidate.pdf"
    pdf.write_bytes(b"placeholder")
    monkeypatch.setattr("src.pipeline.parse_pdf", lambda path: ParsedResume("Ada Lovelace\nada@example.com\nBuilt Python RAG pipeline with embeddings and vector search", []))

    report = run_pipeline(tmp_path, load_settings(), llm=FailingLLM())

    assert report.summary.eligible_candidates == 1
    assert any("LLM enrichment unavailable" in error for error in report.candidates[0].errors)
