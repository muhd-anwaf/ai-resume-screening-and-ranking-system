
from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

from .models import GitHubSummary

load_dotenv()


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._cache: dict[str, GitHubSummary] = {}

        # Use the provided token, or read it from .env
        token = token or os.getenv("GITHUB_TOKEN")

        self._headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "resume-screening-assignment",
        }

        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    

    def enrich(self, username: str | None) -> GitHubSummary:
        if not username:
            return GitHubSummary(status="not_provided", message="No GitHub profile URL found in resume.")
        if username in self._cache:
            return self._cache[username]
        try:
            user_response = requests.get(f"https://api.github.com/users/{username}", headers=self._headers, timeout=self._timeout_seconds)
            if user_response.status_code == 404:
                result = GitHubSummary(status="not_found", username=username, message="Public GitHub profile was not found.")
            elif user_response.status_code != 200:
                result = GitHubSummary(status="unavailable", username=username, message=f"GitHub API returned HTTP {user_response.status_code}.")
            else:
                user: dict[str, Any] = user_response.json()
                repos = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100", headers=self._headers, timeout=self._timeout_seconds)
                events = requests.get(f"https://api.github.com/users/{username}/events/public?per_page=30", headers=self._headers, timeout=self._timeout_seconds)
                repo_data = repos.json() if repos.status_code == 200 else []
                event_data = events.json() if events.status_code == 200 else []
                relevant = [repo.get("name", "") for repo in repo_data if any(key in ((repo.get("description") or "") + " " + repo.get("name", "")).lower() for key in ("ai", "llm", "rag", "python", "agent"))][:5]
                pushes = sum(1 for event in event_data if event.get("type") == "PushEvent")
                result = GitHubSummary(status="enriched", username=username, public_repos=user.get("public_repos"), recent_push_events=pushes, relevant_repositories=relevant)
        except requests.RequestException as exc:
            result = GitHubSummary(status="unavailable", username=username, message=f"GitHub request failed: {exc}")
        self._cache[username] = result
        return result
