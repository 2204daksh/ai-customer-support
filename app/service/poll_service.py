from app.clients.github import GitHubClient
from app.core.config import settings
from app.poller import poll_once


def run_poll() -> dict:
    """Dispatch the poller through GitHub Actions when configured, else run locally."""
    if settings.github_token and settings.github_repo:
        return _trigger_github_poll()
    return _poll_messages()


def _poll_messages() -> dict:
    """Run the poller once directly (local development)."""
    return {"messages": poll_once()}


def _trigger_github_poll() -> dict:
    """Tell GitHub Actions to start the poller workflow (production)."""
    try:
        response = GitHubClient().trigger_poller()
    except Exception as request_error:
        return {"error": f"Failed to contact GitHub API: {str(request_error)}"}

    if response.status_code == 204:
        return {
            "status": "triggered",
            "message": "Poller started via GitHub Actions",
        }

    return {
        "error": f"GitHub API returned status {response.status_code}: {response.text}"
    }
