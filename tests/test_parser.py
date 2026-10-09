from pathlib import Path

import pytest
import pymupdf

from src.parser import ResumeParseError, extract_pdf_text, parse_pdf


def test_extract_pdf_text_remains_text_only_compatibility_wrapper(tmp_path: Path) -> None:
    path = tmp_path / "resume.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Resume text")
    document.save(path)
    document.close()

    assert extract_pdf_text(path) == "Resume text\n"


def test_malformed_pdf_raises_domain_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(ResumeParseError):
        parse_pdf(path)
