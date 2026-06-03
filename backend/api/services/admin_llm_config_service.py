"""Admin LLM-Konfiguration: lesen, speichern, Preview."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.services.prompt_loader import load_prompt
from backend.api.schemas.admin_llm_config import (
    AdminLlmConfigResponse,
    AdminLlmConfigUpdateRequest,
    AdminLlmPreviewRequest,
    AdminLlmPreviewResponse,
)
from backend.core.config.factory import AppContext
from backend.core.config.settings import Settings
from backend.core.models.email import StoredEmail
from backend.infrastructure.repositories.platform_llm_config_repository import (
    PlatformLlmConfigRecord,
)


def _to_response(record: PlatformLlmConfigRecord) -> AdminLlmConfigResponse:
    return AdminLlmConfigResponse(
        classify_temperature=record.classify_temperature,
        extract_temperature=record.extract_temperature,
        draft_temperature=record.draft_temperature,
        similarity_top_k=record.similarity_top_k,
        classify_prompt_override=record.classify_prompt_override,
        extract_prompt_override=record.extract_prompt_override,
        draft_prompt_override=record.draft_prompt_override,
        default_classify_prompt=load_prompt("booking/classify.md"),
        default_extract_prompt=load_prompt("booking/extract.md"),
        default_draft_prompt=load_prompt("booking/draft.md"),
        updated_at=record.updated_at.isoformat(),
        updated_by_user_id=record.updated_by_user_id,
    )


def get_llm_config(ctx: AppContext) -> AdminLlmConfigResponse:
    return _to_response(ctx.platform_llm_config_repo.get_or_default())


def update_llm_config(
    ctx: AppContext,
    body: AdminLlmConfigUpdateRequest,
    *,
    user_id: str | None,
) -> AdminLlmConfigResponse:
    record = PlatformLlmConfigRecord(
        classify_temperature=body.classify_temperature,
        extract_temperature=body.extract_temperature,
        draft_temperature=body.draft_temperature,
        similarity_top_k=body.similarity_top_k,
        classify_prompt_override=_empty_to_none(body.classify_prompt_override),
        extract_prompt_override=_empty_to_none(body.extract_prompt_override),
        draft_prompt_override=_empty_to_none(body.draft_prompt_override),
    )
    saved = ctx.platform_llm_config_repo.save(record, updated_by_user_id=user_id)
    ctx.admin_audit_log_repo.append(
        "llm_config_update",
        user_id=user_id,
        details={
            "classify_temperature": saved.classify_temperature,
            "extract_temperature": saved.extract_temperature,
            "draft_temperature": saved.draft_temperature,
            "similarity_top_k": saved.similarity_top_k,
            "has_classify_override": bool(saved.classify_prompt_override),
            "has_extract_override": bool(saved.extract_prompt_override),
            "has_draft_override": bool(saved.draft_prompt_override),
        },
    )
    return _to_response(saved)


def preview_llm_config(
    ctx: AppContext,
    settings: Settings,
    body: AdminLlmPreviewRequest,
) -> AdminLlmPreviewResponse:
    email = StoredEmail(
        message_id="admin-preview",
        from_address="guest@example.com",
        subject=body.subject,
        body_text=body.body,
        received_at=datetime.now(UTC),
        correlation_id="admin-preview",
    )
    nodes = ctx.workflow._nodes  # noqa: SLF001
    if body.step == "classify":
        intent = nodes._classification.classify(email)  # noqa: SLF001
        return AdminLlmPreviewResponse(
            step="classify",
            result=intent.value,
            model=settings.openai_model_classify,
        )
    extraction = nodes._extraction.extract(email)  # noqa: SLF001
    return AdminLlmPreviewResponse(
        step="extract",
        result=extraction.model_dump_json(),
        model=settings.openai_model_extract,
    )


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
