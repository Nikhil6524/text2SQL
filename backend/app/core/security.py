from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import HTTPException

from app.core.config import settings


@dataclass
class SessionRecord:
    username: str
    expires_at: datetime


class SessionManager:
    def __init__(self, ttl_minutes: int) -> None:
        self._ttl_minutes = ttl_minutes
        self._sessions: Dict[str, SessionRecord] = {}
        self._lock = threading.Lock()

    def create_token(self, username: str) -> dict[str, str]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self._ttl_minutes)
        with self._lock:
            self._sessions[token] = SessionRecord(username=username, expires_at=expires_at)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat(),
        }

    def validate(self, token: str) -> str:
        with self._lock:
            record = self._sessions.get(token)
            if not record:
                raise HTTPException(status_code=401, detail="Invalid token")
            if record.expires_at < datetime.now(timezone.utc):
                self._sessions.pop(token, None)
                raise HTTPException(status_code=401, detail="Token expired")
            return record.username


session_manager = SessionManager(ttl_minutes=settings.token_ttl_minutes)


def authenticate_credentials(username: str, password: str) -> bool:
    return username == settings.login_username and password == settings.login_password


def validate_bearer_header(authorization: str) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1].strip()
    return session_manager.validate(token)
