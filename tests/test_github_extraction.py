from pathlib import Path

import pymupdf

from src.extractor import extract_candidate
from src.parser import parse_pdf


def make_pdf(path: Path, visible_text: str, links: list[tuple[pymupdf.Rect, str]]) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), visible_text)
    for rect, uri in links:
        page.insert_link({"kind": pymupdf.LINK_URI, "from": rect, "uri": uri})
    document.save(path)
    document.close()


def extract_from_pdf(path: Path):
    parsed = parse_pdf(path)
    return extract_candidate(parsed.text, path.name, parsed.hyperlink_uris)


def test_visible_github_url_is_normalized_and_selected(tmp_path: Path) -> None:
    path = tmp_path / "visible.pdf"
    make_pdf(path, "GitHub: www.github.com/ada-lovelace.", [])

    candidate = extract_from_pdf(path)

    assert candidate.github_profile_url == "https://github.com/ada-lovelace"
    assert candidate.github_username == "ada-lovelace"
    assert candidate.github_url_evidence[0].source == "visible_text"


def test_clickable_github_label_extracts_hidden_annotation_url(tmp_path: Path) -> None:
    path = tmp_path / "anchor.pdf"
    make_pdf(path, "GitHub", [(pymupdf.Rect(72, 60, 130, 90), "https://github.com/hidden-user?tab=repositories")])

    candidate = extract_from_pdf(path)

    assert candidate.github_profile_url == "https://github.com/hidden-user"
    assert candidate.github_url_evidence[0].source == "pdf_hyperlink"


def test_clickable_icon_without_readable_text_extracts_annotation_url(tmp_path: Path) -> None:
    path = tmp_path / "icon.pdf"
    make_pdf(path, "Resume", [(pymupdf.Rect(200, 60, 220, 80), "http://github.com/icon-user")])

    candidate = extract_from_pdf(path)

    assert candidate.github_username == "icon-user"
    assert candidate.github_url_evidence[0].source == "pdf_hyperlink"


def test_visible_and_embedded_urls_are_merged_with_provenance(tmp_path: Path) -> None:
    path = tmp_path / "both.pdf"
    make_pdf(path, "github.com/visible-user", [(pymupdf.Rect(72, 60, 220, 90), "https://github.com/anchor-user")])

    candidate = extract_from_pdf(path)

    assert {item.source for item in candidate.github_url_evidence} == {"visible_text", "pdf_hyperlink"}
    assert candidate.github_username == "visible-user"


def test_repository_url_is_preserved_but_not_mistaken_for_profile() -> None:
    candidate = extract_candidate("https://github.com/an-org/a-project", "resume.pdf")

    assert candidate.github_username is None
    assert candidate.github_url_evidence[0].normalized_url == "https://github.com/an-org"
    assert candidate.github_url_evidence[0].is_profile_candidate is False
    assert "Repository" in (candidate.github_url_evidence[0].detail or "")


def test_repository_url_in_pdf_is_not_selected_as_profile(tmp_path: Path) -> None:
    path = tmp_path / "repository.pdf"
    make_pdf(path, "Projects: https://github.com/an-org/a-project", [])

    candidate = extract_from_pdf(path)

    assert candidate.github_username is None
    assert candidate.github_url_evidence[0].is_profile_candidate is False
    assert candidate.github_url_evidence[0].source == "visible_text"


def test_no_github_link_produces_no_profile_evidence() -> None:
    candidate = extract_candidate("Ada Lovelace\nada@example.com", "resume.pdf")

    assert candidate.github_username is None
    assert candidate.github_url_evidence == []


def test_pdf_without_github_links_produces_no_profile_evidence(tmp_path: Path) -> None:
    path = tmp_path / "missing.pdf"
    make_pdf(path, "Ada Lovelace\nada@example.com", [])

    candidate = extract_from_pdf(path)

    assert candidate.github_username is None
    assert candidate.github_url_evidence == []


def test_matching_visible_and_embedded_urls_are_deduplicated(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.pdf"
    make_pdf(path, "GitHub: https://github.com/ada-lovelace", [
        (pymupdf.Rect(72, 60, 220, 90), "https://www.github.com/ada-lovelace?tab=repositories")
    ])

    candidate = extract_from_pdf(path)

    assert candidate.github_username == "ada-lovelace"
    assert len(candidate.github_url_evidence) == 1
    assert candidate.github_url_evidence[0].source == "visible_text"


def test_unrelated_annotation_is_not_a_github_profile(tmp_path: Path) -> None:
    path = tmp_path / "external.pdf"
    make_pdf(path, "Portfolio", [(pymupdf.Rect(72, 60, 140, 90), "https://example.com/portfolio")])

    candidate = extract_from_pdf(path)

    assert candidate.github_username is None
    assert candidate.github_url_evidence[0].source == "pdf_hyperlink"
    assert candidate.github_url_evidence[0].detail == "Not a GitHub host."
