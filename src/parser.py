"""PDF parsing with file-level error isolation."""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from pathlib import Path


class ResumeParseError(RuntimeError):
    """Raised when a specific resume cannot be opened or read."""


@dataclass(frozen=True)
class ParsedResume:
    text: str
    hyperlink_uris: list[str]


def parse_pdf(path: Path) -> ParsedResume:
    """Extract text and URI annotations from a resume PDF.

    Annotation URIs are independent of visible text, allowing links behind a
    label, icon, or logo to be recovered without trusting the annotation label.
    """
    try:
        import pymupdf

        library_stderr = io.StringIO()
        with contextlib.redirect_stderr(library_stderr):
            with pymupdf.open(path) as document:
                if document.page_count == 0:
                    raise ResumeParseError("PDF has no pages.")
                page_text: list[str] = []
                hyperlink_uris: list[str] = []
                for page in document:
                    extracted_text = page.get_text("text")
                    if not isinstance(extracted_text, str):
                        raise ResumeParseError("PDF page did not return text.")
                    page_text.append(extracted_text)
                    for link in page.get_links():
                        uri = link.get("uri")
                        if not isinstance(uri, str):
                            continue
                        uri = uri.strip()
                        if uri:
                            hyperlink_uris.append(uri)
                text = "\n".join(page_text)
    except ResumeParseError:
        raise
    except Exception as exc:  # library errors vary by malformed-PDF type
        raise ResumeParseError(f"Unable to read PDF: {exc}") from exc

    if not text.strip():
        detail = library_stderr.getvalue().strip()
        suffix = f" MuPDF diagnostics: {detail[:500]}" if detail else ""
        raise ResumeParseError("PDF contains no extractable text (possibly scanned)." + suffix)
    return ParsedResume(text=text, hyperlink_uris=hyperlink_uris)


def extract_pdf_text(path: Path) -> str:
    """Compatibility wrapper for callers that need only visible text."""
    return parse_pdf(path).text
