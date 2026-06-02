"""Langfuse-Konfiguration für PII-arme @observe-Traces mit SDK v2."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config.settings import Settings


def tracing_enabled(settings: Settings) -> bool:
    """Tracing aktiv wenn Keys gesetzt und nicht Test-Umgebung."""
    if settings.app_env == "test":
        return False
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def configure_langfuse_env(settings: Settings) -> bool:
    """Setze LANGFUSE_* für @observe-Tracing (idempotent)."""
    if not tracing_enabled(settings):
        os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
        return False
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_HOST"] = settings.langfuse_host
    os.environ["LANGFUSE_TRACING_ENABLED"] = "true"
    return True
