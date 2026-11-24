import secrets
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

security = HTTPBasic(auto_error=False)


def require_login(
    credentials: HTTPBasicCredentials | None = Depends(security),
) -> None:
    valid = (
        credentials is not None
        and settings.dashboard_password != ""
        and secrets.compare_digest(credentials.username.encode(), settings.dashboard_username.encode())
        and secrets.compare_digest(credentials.password.encode(), settings.dashboard_password.encode())
    )
    if not valid:
        raise HTTPException(status_code=401, detail="Wrong username or password")
