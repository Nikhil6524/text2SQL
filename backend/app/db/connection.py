from __future__ import annotations

import psycopg2
from fastapi import HTTPException
from psycopg2.extensions import connection as PgConnection

from app.core.config import settings


def get_connection() -> PgConnection:
    if not settings.database_url:
        raise HTTPException(status_code=500, detail="Database is not configured. Add AIVEN_POSTGRES_URL in .env")

    try:
        return psycopg2.connect(settings.database_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {exc}") from exc
