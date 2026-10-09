"""Application configuration kept independent from business logic."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class ScoringWeights:
    ai_project_depth: int = 40
    python_backend: int = 30
    cloud_full_stack: int = 15
    github_activity: int = 10
    engineering_depth: int = 5

    @property
    def total(self) -> int:
        return sum(
            (
                self.ai_project_depth,
                self.python_backend,
                self.cloud_full_stack,
                self.github_activity,
                self.engineering_depth,
            )
        )


@dataclass(frozen=True)
class Settings:
    github_token: str | None
    llm_api_key: str | None
    llm_model: str | None
    scoring: ScoringWeights


def load_settings() -> Settings:
    """Read local configuration without ever requiring secrets."""
    load_dotenv()
    return Settings(
        github_token=os.getenv("GITHUB_TOKEN") or None,
        llm_api_key=os.getenv("LLM_API_KEY") or None,
        llm_model=os.getenv("LLM_MODEL") or None,
        scoring=ScoringWeights(),
    )

