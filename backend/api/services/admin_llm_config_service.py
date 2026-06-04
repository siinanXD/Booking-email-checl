"""Admin LLM-Konfiguration: lesen, speichern, Preview."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.ai.services.classification import ClassificationService
from backend.ai.services.extraction import ExtractionService
from backend.ai.services.llm_errors import LLM_PIPELINE_ERRORS
from backend.ai.services.prompt_loader import load_prompt
from backend.api.schemas.admin_llm_config import (
    AdminLlmConfigResponse,
    AdminLlmConfigUpdateRequest,
    AdminLlmPreviewRequest,
    AdminLlmPreviewResponse,
    AdminLlmPromptHistoryEntry,
    AdminLlmPromptHistoryResponse,
    LlmPreviewStep,
    LlmPromptType,
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
    previous = ctx.platform_llm_config_repo.get_or_default()
    classify_override = _empty_to_none(body.classify_prompt_override)
    extract_override = _empty_to_none(body.extract_prompt_override)
    draft_override = _empty_to_none(body.draft_prompt_override)

    _record_prompt_history_if_changed(
        ctx,
        "classify",
        previous.classify_prompt_override,
        classify_override,
        user_id=user_id,
    )
    _record_prompt_history_if_changed(
        ctx,
        "extract",
        previous.extract_prompt_override,
        extract_override,
        user_id=user_id,
    )
    _record_prompt_history_if_changed(
        ctx,
        "draft",
        previous.draft_prompt_override,
        draft_override,
        user_id=user_id,
    )

    record = PlatformLlmConfigRecord(
        classify_temperature=body.classify_temperature,
        extract_temperature=body.extract_temperature,
        draft_temperature=body.draft_temperature,
        similarity_top_k=body.similarity_top_k,
        classify_prompt_override=classify_override,
        extract_prompt_override=extract_override,
        draft_prompt_override=draft_override,
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


def get_prompt_history(
    ctx: AppContext,
    prompt_type: LlmPromptType,
    *,
    limit: int = 15,
) -> AdminLlmPromptHistoryResponse:
    entries = ctx.platform_llm_prompt_history_repo.list_by_type(
        prompt_type,
        limit=limit,
    )
    return AdminLlmPromptHistoryResponse(
        prompt_type=prompt_type,
        entries=[
            AdminLlmPromptHistoryEntry(
                id=entry.id,
                prompt_type=entry.prompt_type,
                prompt_text=entry.prompt_text,
                user_id=entry.user_id,
                created_at=entry.created_at.isoformat(),
            )
            for entry in entries
        ],
    )


def _record_prompt_history_if_changed(
    ctx: AppContext,
    prompt_type: LlmPromptType,
    previous: str | None,
    current: str | None,
    *,
    user_id: str | None,
) -> None:
    if previous == current:
        return
    ctx.platform_llm_prompt_history_repo.append(
        prompt_type,
        current,
        user_id=user_id,
    )


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
    classification = nodes._classification  # noqa: SLF001
    extraction = nodes._extraction  # noqa: SLF001
    if body.step == "classify":
        return _preview_classify(classification, email, body.step)
    return _preview_extract(extraction, email, body.step)


def _preview_classify(
    svc: ClassificationService,
    email: StoredEmail,
    step: LlmPreviewStep,
) -> AdminLlmPreviewResponse:
    from backend.ai.services.prompt_loader import format_resolved_prompt_with_few_shots

    config = (
        svc._llm_config_repo.get_or_default()  # noqa: SLF001
        if svc._llm_config_repo is not None
        else None
    )
    prompt = format_resolved_prompt_with_few_shots(
        "booking/classify.md",
        "booking/examples/classify_examples.json",
        config.classify_prompt_override if config else None,
        subject=email.subject,
        from_address=email.from_address,
        body=email.body_text,
    )
    try:
        temperature = config.classify_temperature if config else None
        completion = svc._llm.complete(  # noqa: SLF001
            prompt,
            svc._model,  # noqa: SLF001
            temperature=temperature,
        )
        slug = completion.text.strip().lower().replace(" ", "_")
        try:
            intent = BookingIntent(slug)
        except ValueError:
            intent = BookingIntent.OTHER
        return AdminLlmPreviewResponse(
            step=step,
            success=True,
            result=intent.value,
            error=None,
            model=svc._model,  # noqa: SLF001
        )
    except LLM_PIPELINE_ERRORS as exc:
        return AdminLlmPreviewResponse(
            step=step,
            success=False,
            result=None,
            error=_humanize_llm_error(exc),
            model=svc._model,  # noqa: SLF001
        )


def _preview_extract(
    svc: ExtractionService,
    email: StoredEmail,
    step: LlmPreviewStep,
) -> AdminLlmPreviewResponse:
    from backend.ai.services.prompt_loader import format_resolved_prompt_with_few_shots

    config = (
        svc._llm_config_repo.get_or_default()  # noqa: SLF001
        if svc._llm_config_repo is not None
        else None
    )
    prompt = format_resolved_prompt_with_few_shots(
        "booking/extract.md",
        "booking/examples/extract_examples.json",
        config.extract_prompt_override if config else None,
        few_shot_style="extract",
        subject=email.subject,
        body=email.body_text,
    )
    try:
        temperature = config.extract_temperature if config else None
        completion = svc._llm.complete(  # noqa: SLF001
            prompt,
            svc._model,  # noqa: SLF001
            temperature=temperature,
        )
        data = svc._parse_json(completion.text)  # noqa: SLF001
        parsed = BookingExtraction.model_validate(data)
        return AdminLlmPreviewResponse(
            step=step,
            success=True,
            result=parsed.model_dump_json(),
            error=None,
            model=svc._model,  # noqa: SLF001
        )
    except LLM_PIPELINE_ERRORS as exc:
        return AdminLlmPreviewResponse(
            step=step,
            success=False,
            result=None,
            error=_humanize_llm_error(exc),
            model=svc._model,  # noqa: SLF001
        )


def _humanize_llm_error(exc: BaseException) -> str:
    message = str(exc)
    lowered = message.lower()
    if "insufficient_quota" in lowered or "exceeded your current quota" in lowered:
        return (
            "OpenAI-Quota aufgebraucht. Bitte Guthaben/Billing prüfen "
            "oder für Tests LLM_MODE=mock in .env setzen und Backend neu starten."
        )
    if "rate limit" in lowered or type(exc).__name__ == "RateLimitError":
        return f"OpenAI Rate-Limit: {message}"
    if isinstance(exc, ValueError) and "json" in lowered:
        return f"LLM-Antwort ist kein gültiges JSON: {message}"
    return f"{type(exc).__name__}: {message}"


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
