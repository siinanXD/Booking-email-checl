"""Gemini-Konfiguration (Phase C — Workflow-Sandbox)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.config.settings import Settings


def gemini_configured(settings: Settings) -> bool:
    """True wenn GEMINI_API_KEY gesetzt ist."""
    return bool(settings.gemini_api_key.strip())


def gemini_available(settings: Settings) -> bool:
    """Gemini nutzbar: Key gesetzt oder LLM_MODE=mock (MockGemini)."""
    if settings.llm_mode.strip().lower() == "mock":
        return True
    return gemini_configured(settings)
