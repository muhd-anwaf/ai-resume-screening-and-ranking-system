# AI Resume Screening & Ranking System

A resilient Python CLI that screens a directory of PDF resumes, applies deterministic eligibility rules, enriches eligible candidates with public GitHub data, and produces an evidence-based JSON ranking.

## Installation

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`GITHUB_TOKEN` is optional but recommended for higher public GitHub API limits. `LLM_API_KEY` is reserved for a future provider implementation; secrets are never hard-coded.

## Run

Put PDF resumes in `resumes/`, then run:

```powershell
python -m src.main --input .\resumes --output .\output\results.json
```

The report contains every input PDF, including unreadable files and rejected candidates. Eligible candidates are ranked by descending total score.

## Test

```powershell
python -m pytest -q
```

## Design decisions

- **Eligibility:** Python evidence and meaningful AI/LLM/RAG/agentic evidence are evaluated deterministically and separately from scoring. JavaScript, Java, React, and Next.js neither qualify nor disqualify a candidate by themselves.
- **Scoring:** Components are independently capped at 40/30/15/10/5. Scores use explicit extraction evidence and report deductions for shallow AI claims.
- **LLM use:** `ResumeAnalysisAdapter` is a replaceable extension point. The default adapter is disabled, so a missing model key never prevents safe processing. Any provider must return validated Pydantic data and must treat resume text as untrusted data.
- **GitHub:** Visible URLs and embedded PDF links are normalized and deduplicated; only account-profile URLs select a username. The client uses public REST endpoints, caches each username during a run, and returns a status rather than failing the batch for missing profiles, rate limits, or network failures.
- **Reliability:** Each PDF is isolated with its own exception boundary. Errors become report records rather than batch failures.

## If I had more time

1. Add a concrete structured-output LLM provider with prompt-injection-resistant prompts and response validation.
2. Improve project segmentation and support OCR for scanned resumes.
3. Add GitHub request retries with rate-limit reset handling and persistent caching.
4. Add golden PDF fixtures and integration tests for a wider variety of resume layouts.
