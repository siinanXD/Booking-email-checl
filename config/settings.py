"""Zentrale Einstellungen aus Umgebungsvariablen (Pydantic Settings)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Immer Projekt-`.env`, nicht abhaengig vom aktuellen Terminal-Verzeichnis
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Lädt Werte aus `.env`; siehe `.env.example` für alle Keys."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    # live = OpenAI; mock = Dev ohne API-Kosten (Platzhalter-Antworten)
    llm_mode: str = Field(default="live", alias="LLM_MODE")
    mongodb_uri: str = Field(alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="ai_email", alias="MONGODB_DB_NAME")

    langfuse_public_key: str = Field(alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        alias="LANGFUSE_HOST",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    human_review_required: bool = Field(default=True, alias="HUMAN_REVIEW_REQUIRED")

    openai_model_classify: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_MODEL_CLASSIFY",
    )
    openai_model_extract: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_MODEL_EXTRACT",
    )
    openai_model_draft: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_DRAFT")
    embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    max_tokens_per_mail: int = Field(default=8000, alias="MAX_TOKENS_PER_MAIL")
    webhook_alert_url: str | None = Field(default=None, alias="WEBHOOK_ALERT_URL")
    langgraph_checkpoint_uri: str | None = Field(
        default=None,
        alias="LANGGRAPH_CHECKPOINT_URI",
    )

    azure_tenant_id: str | None = Field(default=None, alias="AZURE_TENANT_ID")
    azure_client_id: str | None = Field(default=None, alias="AZURE_CLIENT_ID")
    azure_client_secret: str | None = Field(default=None, alias="AZURE_CLIENT_SECRET")
    azure_authority: str = Field(default="common", alias="AZURE_AUTHORITY")
    outlook_mailbox: str | None = Field(default=None, alias="OUTLOOK_MAILBOX")
    outlook_auth_mode: str = Field(default="delegated", alias="OUTLOOK_AUTH_MODE")
    outlook_token_cache_path: str = Field(
        default=".outlook_token_cache.json",
        alias="OUTLOOK_TOKEN_CACHE_PATH",
    )
    outlook_post_action: str = Field(default="none", alias="OUTLOOK_POST_ACTION")
    outlook_processed_folder: str | None = Field(
        default=None,
        alias="OUTLOOK_PROCESSED_FOLDER",
    )
    outlook_fetch_max: int = Field(default=100, alias="OUTLOOK_FETCH_MAX")
    outlook_fetch_unread_only: bool = Field(
        default=False,
        alias="OUTLOOK_FETCH_UNREAD_ONLY",
    )


def get_settings() -> Settings:
    """Factory für Settings; lädt Werte aus Umgebung / `.env`."""
    return Settings.model_validate({})
