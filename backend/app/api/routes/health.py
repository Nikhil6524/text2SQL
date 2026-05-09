from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "database_configured": bool(settings.database_url),
        "groq_configured": bool(settings.groq_api_key),
        "model": settings.groq_model,
    }
