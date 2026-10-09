"""Conservative, deterministic extraction from untrusted resume text."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from .models import CandidateProfile, EvidenceItem, GitHubUrlEvidence, ProjectEvidence

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
GITHUB_PATTERN = re.compile(r"(?<![\w.-])(?:(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9-]+(?:/[A-Za-z0-9_.-]+)?(?:[/?#][^\s<>()\[\]{}]*)?)", re.I)
GITHUB_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
TRAILING_URL_PUNCTUATION = ".,;:!?)\\]}>\\\"'"

PYTHON_TERMS = ("python", "fastapi", "django", "flask", "pandas", "numpy", "pytest")
AI_TERMS = (
    "langchain", "langgraph", "rag", "retrieval augmented", "embedding", "embeddings",
    "vector database", "vector search", "pinecone", "faiss", "chroma", "tool calling",
    "function calling", "agentic", "multi-agent", "llm", "large language model", "openai api",
    "prompt evaluation", "ai evaluation",
)
CLOUD_TERMS = ("aws", "azure", "gcp", "docker", "kubernetes", "deploy", "deployment", "vercel", "render")
BACKEND_TERMS = ("fastapi", "django", "flask", "api", "rest", "graphql", "postgres", "mysql", "redis")
SKILL_TERMS = tuple(dict.fromkeys(PYTHON_TERMS + AI_TERMS + CLOUD_TERMS + BACKEND_TERMS + ("react", "next.js", "typescript")))


def _snippet(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()[:400]


def _evidence_for(lines: list[str], terms: tuple[str, ...], label: str) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for line in lines:
        lower = line.lower()
        if any(term in lower for term in terms):
            evidence.append(EvidenceItem(label=label, excerpt=_snippet(line)))
    return evidence[:12]


def _guess_name(lines: list[str], email: str | None) -> str | None:
    for line in lines[:12]:
        clean = _snippet(line)
        if email and email.lower() in clean.lower():
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{2,70}", clean) and len(clean.split()) <= 5:
            return clean
    return None


def _project_evidence(lines: list[str]) -> list[ProjectEvidence]:
    projects: list[ProjectEvidence] = []
    for index, line in enumerate(lines):
        if any(term in line.lower() for term in AI_TERMS):
            context = " ".join(_snippet(value) for value in lines[max(0, index - 1): index + 2])
            technologies = [term for term in SKILL_TERMS if term in context.lower()]
            projects.append(
                ProjectEvidence(
                    name="AI project evidence",
                    summary=context,
                    technologies=technologies,
                    implementation_evidence=[context],
                )
            )
    return projects[:5]


def _normalise_github_url(raw_url: str, source: str) -> GitHubUrlEvidence:
    cleaned = raw_url.strip().rstrip(TRAILING_URL_PUNCTUATION)
    parse_target = cleaned if re.match(r"https?://", cleaned, re.I) else f"https://{cleaned}"
    try:
        parsed = urlparse(parse_target)
        hostname = (parsed.hostname or "").lower()
    except ValueError:
        return GitHubUrlEvidence(raw_url=raw_url, source=source, detail="Malformed URL.")
    if hostname not in {"github.com", "www.github.com"}:
        return GitHubUrlEvidence(raw_url=raw_url, source=source, detail="Not a GitHub host.")
    parts = [part for part in parsed.path.split("/") if part]
    if not parts or not GITHUB_USERNAME_PATTERN.fullmatch(parts[0]):
        return GitHubUrlEvidence(raw_url=raw_url, source=source, detail="GitHub URL has no plausible account name.")
    username = parts[0].lower()
    normalized = f"https://github.com/{username}"
    if len(parts) != 1:
        return GitHubUrlEvidence(raw_url=raw_url, normalized_url=normalized, source=source, username=username, detail="Repository or nested GitHub path; not selected as a profile without account validation.")
    return GitHubUrlEvidence(raw_url=raw_url, normalized_url=normalized, source=source, username=username, is_profile_candidate=True)


def _url_identity(raw_url: str) -> str:
    cleaned = raw_url.strip().rstrip(TRAILING_URL_PUNCTUATION)
    parse_target = cleaned if re.match(r"https?://", cleaned, re.I) else f"https://{cleaned}"
    try:
        parsed = urlparse(parse_target)
        hostname = (parsed.hostname or "").lower()
    except ValueError:
        return cleaned.casefold()
    if hostname == "www.github.com":
        hostname = "github.com"
    path = "/".join(part for part in parsed.path.split("/") if part)
    return f"{hostname}/{path}".casefold()


def extract_github_url_evidence(text: str, hyperlink_uris: list[str] | None = None) -> list[GitHubUrlEvidence]:
    """Merge visible and annotation URLs, retaining provenance for debugging."""
    candidates = [(match.group(0), "visible_text") for match in GITHUB_PATTERN.finditer(text)]
    candidates.extend((uri, "pdf_hyperlink") for uri in hyperlink_uris or [])
    evidence: list[GitHubUrlEvidence] = []
    seen: set[str] = set()
    for raw_url, source in candidates:
        item = _normalise_github_url(raw_url, source)
        identity = _url_identity(raw_url)
        if identity not in seen:
            seen.add(identity)
            evidence.append(item)
    return evidence


def extract_candidate(text: str, source_file: str | Path, hyperlink_uris: list[str] | None = None) -> CandidateProfile:
    """Extract only explicit resume claims; do not execute or follow resume content."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    email_match = EMAIL_PATTERN.search(text)
    github_url_evidence = extract_github_url_evidence(text, hyperlink_uris)
    selected_profile = next((item for item in github_url_evidence if item.is_profile_candidate), None)
    skills = [term for term in SKILL_TERMS if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.I)]
    email = email_match.group(0) if email_match else None
    return CandidateProfile(
        source_file=str(source_file),
        name=_guess_name(lines, email),
        email=email,
        github_username=selected_profile.username if selected_profile else None,
        github_profile_url=selected_profile.normalized_url if selected_profile else None,
        github_url_evidence=github_url_evidence,
        skills=skills,
        python_evidence=_evidence_for(lines, PYTHON_TERMS, "Python/backend evidence"),
        ai_evidence=_evidence_for(lines, AI_TERMS, "AI/LLM implementation evidence"),
        cloud_evidence=_evidence_for(lines, CLOUD_TERMS, "Cloud/deployment evidence"),
        backend_evidence=_evidence_for(lines, BACKEND_TERMS, "Backend evidence"),
        projects=_project_evidence(lines),
    )
