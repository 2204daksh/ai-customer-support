import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env into the environment.
load_dotenv()


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    database_url: str
    classifier_model: str = "google:gemini-3.1-flash-lite"
    agent_model: str = "google:gemini-3.1-flash-lite"
    llm_api_key: str
    poll_interval_seconds: int = 60
    dashboard_username: str = "admin"
    dashboard_password: str = ""


settings = Settings()

# Expose the LLM API key as GOOGLE_API_KEY so pydantic-ai's Google provider finds it.
if settings.llm_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.llm_api_key)