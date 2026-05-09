import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.stats import router as stats_router
from app.core.config import settings
from app.db.schema import fetch_public_schema
from app.services.schema_rag import schema_rag


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")


@app.on_event("startup")
def rebuild_schema_index() -> None:
    try:
        schema = fetch_public_schema()
        if schema:
            schema_rag.rebuild(schema)
    except Exception as exc:
        logging.warning("Schema RAG rebuild failed: %s", exc)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Conversational DB Assistant is running"}
