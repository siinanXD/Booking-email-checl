"""Admin LLM-Konfiguration API-Schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LlmPreviewStep = Literal["classify", "extract"]


class AdminLlmConfigResponse(BaseModel):
    """Aktuelle globale LLM-Konfiguration."""

    classify_temperature: float = 0.0
    extract_temperature: float = 0.0
    draft_temperature: float = 0.0
    similarity_top_k: int = 3
    classify_prompt_override: str | None = None
    extract_prompt_override: str | None = None
    draft_prompt_override: str | None = None
    default_classify_prompt: str
    default_extract_prompt: str
    default_draft_prompt: str
    updated_at: str | None = None
    updated_by_user_id: str | None = None


class AdminLlmConfigUpdateRequest(BaseModel):
    """PUT-Body für LLM-Konfiguration."""

    classify_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    extract_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    draft_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    similarity_top_k: int = Field(default=3, ge=1, le=20)
    classify_prompt_override: str | None = None
    extract_prompt_override: str | None = None
    draft_prompt_override: str | None = None


class AdminLlmPreviewRequest(BaseModel):
    """Dry-Run auf Beispieltext."""

    step: LlmPreviewStep = "classify"
    subject: str = "Neue Buchung AB123"
    body: str = "Guten Tag, ich habe eine Buchung AB123 vom 12.06. bis 15.06."


class AdminLlmPreviewResponse(BaseModel):
    """Ergebnis eines Dry-Runs."""

    step: LlmPreviewStep
    result: str
    model: str
