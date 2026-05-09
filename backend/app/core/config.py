import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Conversational DB Assistant")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    database_url: str | None = os.getenv("AIVEN_POSTGRES_URL") or os.getenv("DATABASE_URL")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    login_username: str = os.getenv("APP_LOGIN_USERNAME", "admin")
    login_password: str = os.getenv("APP_LOGIN_PASSWORD", "admin123")
    token_ttl_minutes: int = int(os.getenv("TOKEN_TTL_MINUTES", "480"))

    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
