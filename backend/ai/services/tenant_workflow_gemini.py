"""Gemini-Hilfen für Mandanten-Workflow-Sandbox."""

from __future__ import annotations

import json

from backend.ai.services.gemini_client import GeminiClientProtocol
from backend.ai.services.gemini_setup import gemini_available, gemini_configured
from backend.ai.services.llm_errors import LLM_PIPELINE_ERRORS
from backend.ai.services.tenant_workflow_runtime import (
    build_gemini_extract_prompt,
    parse_json_object,
)
from backend.api.schemas.tenant_workflows import TenantWorkflowPreviewResponse
from backend.core.config.settings import Settings
from backend.core.models.workflow_media import (
    WorkflowMediaAttachment,
    attachments_to_media_parts,
)
from backend.infrastructure.repositories.tenant_workflow_repository import (
    TenantWorkflowRecord,
)


def gemini_missing_key_error() -> str:
    return (
        "GEMINI_API_KEY fehlt. Trage den Key in .env ein (Google AI Studio → API Keys)."
    )


def run_gemini_extract_preview(
    *,
    gemini: GeminiClientProtocol,
    settings: Settings,
    record: TenantWorkflowRecord,
    subject: str,
    body: str,
    attachments: list[WorkflowMediaAttachment] | None,
) -> TenantWorkflowPreviewResponse:
    model = settings.gemini_model_extract
    prompt = build_gemini_extract_prompt(record, subject, body)
    if not prompt.strip():
        return TenantWorkflowPreviewResponse(
            success=False,
            result=None,
            error="Extraktions- oder Multimodal-Prompt ist leer.",
            model=model,
        )
    media = attachments_to_media_parts(attachments)
    notice: str | None = None
    try:
        if record.supports_multimodal and media:
            completion = gemini.complete_multimodal(
                prompt,
                model,
                media,
                temperature=0.0,
            )
        else:
            if record.supports_multimodal and not media:
                notice = (
                    "Keine Anhänge im Request — Gemini nutzt nur Text. "
                    "Bilder/PDF in Preview hochladen für Multimodal."
                )
            completion = gemini.complete_text(prompt, model, temperature=0.0)
        parsed = parse_json_object(completion.text)
        return TenantWorkflowPreviewResponse(
            success=True,
            result=json.dumps(parsed, ensure_ascii=False, indent=2),
            error=None,
            model=model,
            notice=notice,
        )
    except LLM_PIPELINE_ERRORS as exc:
        return TenantWorkflowPreviewResponse(
            success=False,
            result=None,
            error=str(exc),
            model=model,
        )


def resolve_gemini_for_preview(
    settings: Settings,
    gemini: GeminiClientProtocol | None,
) -> TenantWorkflowPreviewResponse | None:
    """Fehler-Response wenn Gemini angefordert aber nicht verfügbar."""
    if gemini is not None:
        return None
    if settings.llm_mode.strip().lower() == "mock":
        return TenantWorkflowPreviewResponse(
            success=False,
            result=None,
            error="Gemini-Mock nicht geladen.",
            model=settings.gemini_model_extract,
        )
    if not gemini_configured(settings):
        return TenantWorkflowPreviewResponse(
            success=False,
            result=None,
            error=gemini_missing_key_error(),
            model=settings.gemini_model_extract,
        )
    return TenantWorkflowPreviewResponse(
        success=False,
        result=None,
        error="Gemini-Client nicht initialisiert.",
        model=settings.gemini_model_extract,
    )


def gemini_ready(settings: Settings, gemini: GeminiClientProtocol | None) -> bool:
    return gemini is not None and gemini_available(settings)
