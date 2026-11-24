import httpx

from app.core.config import settings

GITHUB_API_BASE_URL = "https://api.github.com"
POLLER_WORKFLOW = "poller.yml"
MAIN_BRANCH = "main"


class GitHubClient:
    """Calls the GitHub Actions API for the configured repository."""

    def trigger_poller(self) -> httpx.Response:
        """Dispatch the poller workflow and return the raw response."""
        with httpx.Client(
            base_url=GITHUB_API_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        ) as http_client:
            return http_client.post(
                f"/repos/{settings.github_repo}/actions/workflows/{POLLER_WORKFLOW}/dispatches",
                json={"ref": MAIN_BRANCH},
            )
