"""Interne Hilfen für Mandanten-Workflows."""

from __future__ import annotations

import json
import re

from backend.ai.services.llm_errors import LLM_PIPELINE_ERRORS
from backend.ai.services.tenant_workflow_gemini import (
    gemini_ready,
    resolve_gemini_for_preview,
    run_gemini_extract_preview,
)
from backend.ai.services.tenant_workflow_runtime import (
    format_extract_prompt,
    parse_json_object,
)
from backend.api.schemas.tenant_workflows import (
    TenantWorkflowCreateRequest,
    TenantWorkflowPreviewResponse,
    TenantWorkflowResponse,
    TenantWorkflowSummary,
    TenantWorkflowUpdateRequest,
    WorkflowFewShotExampleSchema,
    WorkflowMatchRulesSchema,
    WorkflowTestEmailSchema,
)
from backend.core.config.factory import AppContext
from backend.core.config.settings import Settings
from backend.core.models.workflow_media import WorkflowMediaAttachment
from backend.infrastructure.repositories.tenant_workflow_repository import (
    TenantWorkflowRecord,
    WorkflowFewShotExample,
    WorkflowMatchRules,
    WorkflowTestEmail,
    slugify_label,
)


def _run_extract_preview(
    ctx: AppContext,
    settings: Settings,
    record: TenantWorkflowRecord,
    subject: str,
    body: str,
    attachments: list[WorkflowMediaAttachment] | None = None,
) -> TenantWorkflowPreviewResponse:
    if record.llm_provider == "gemini":
        if not gemini_ready(settings, ctx.gemini_client):
            blocked = resolve_gemini_for_preview(settings, ctx.gemini_client)
            if blocked is not None:
                return blocked
        assert ctx.gemini_client is not None
        return run_gemini_extract_preview(
            gemini=ctx.gemini_client,
            settings=settings,
            record=record,
            subject=subject,
            body=body,
            attachments=attachments,
        )
    if not record.extract_prompt.strip():
        return TenantWorkflowPreviewResponse(
            success=False,
            result=None,
            error="Extraktions-Prompt ist leer.",
            model=settings.openai_model_extract,
        )
    prompt = format_extract_prompt(record, subject, body)
    llm = ctx.workflow._nodes._extraction._llm  # noqa: SLF001
    model = settings.openai_model_extract
    try:
        completion = llm.complete(prompt, model, temperature=0.0)
        parsed = parse_json_object(completion.text)
        return TenantWorkflowPreviewResponse(
            success=True,
            result=json.dumps(parsed, ensure_ascii=False, indent=2),
            error=None,
            model=model,
        )
    except LLM_PIPELINE_ERRORS as exc:
        return TenantWorkflowPreviewResponse(
            success=False,
            result=None,
            error=f"{type(exc).__name__}: {exc}",
            model=model,
        )


def _definition_changed(
    existing: TenantWorkflowRecord,
    body: TenantWorkflowUpdateRequest,
) -> bool:
    if existing.classify_prompt.strip() != (body.classify_prompt or "").strip():
        return True
    if existing.extract_prompt.strip() != (body.extract_prompt or "").strip():
        return True
    existing_tests = [(t.subject, t.body) for t in existing.test_emails]
    body_tests = [(t.subject, t.body) for t in body.test_emails]
    return existing_tests != body_tests


def _resolve_slug(
    slug: str | None,
    label: str,
    *,
    fallback: str | None = None,
) -> str:
    candidate = (slug or "").strip() or slugify_label(label) or fallback or "workflow"
    candidate = re.sub(r"[^a-z0-9_]", "", candidate.lower())
    return candidate or "workflow"


def _record_from_request(
    body: TenantWorkflowCreateRequest | TenantWorkflowUpdateRequest,
    *,
    account_id: str,
    slug: str,
    workflow_id: str | None = None,
) -> TenantWorkflowRecord:
    return TenantWorkflowRecord(
        id=workflow_id or "",
        account_id=account_id,
        slug=slug,
        label=body.label.strip(),
        description=body.description.strip(),
        enabled=body.enabled,
        sandbox_only=body.sandbox_only,
        priority=body.priority,
        search_hints=body.search_hints.strip(),
        importance=body.importance,
        required_fields=list(body.required_fields),
        optional_fields=list(body.optional_fields),
        extraction_schema=dict(body.extraction_schema),
        classify_prompt=body.classify_prompt.strip(),
        extract_prompt=body.extract_prompt.strip(),
        draft_prompt=body.draft_prompt.strip(),
        few_shot_examples=[
            WorkflowFewShotExample(
                subject=item.subject,
                body=item.body,
                expected_json=dict(item.expected_json),
            )
            for item in body.few_shot_examples
        ],
        test_emails=[
            WorkflowTestEmail(
                subject=item.subject,
                body=item.body,
                expected_fields=item.expected_fields,
                attachments=list(item.attachments),
            )
            for item in body.test_emails
        ],
        match_rules=WorkflowMatchRules(
            subject_keywords=list(body.match_rules.subject_keywords),
            from_domains=list(body.match_rules.from_domains),
            body_keywords=list(body.match_rules.body_keywords),
        ),
        llm_provider=body.llm_provider,
        supports_multimodal=body.supports_multimodal,
        multimodal_prompt=body.multimodal_prompt.strip(),
    )


def _to_summary(record: TenantWorkflowRecord) -> TenantWorkflowSummary:
    return TenantWorkflowSummary(
        id=record.id,
        slug=record.slug,
        label=record.label,
        description=record.description,
        enabled=record.enabled,
        sandbox_only=record.sandbox_only,
        importance=record.importance,
        supports_multimodal=record.supports_multimodal,
        test_email_count=len(record.test_emails),
        tests_passed=bool(
            record.last_test_passed_at
            and record.last_test_passed_total > 0
            and record.last_test_passed_count == record.last_test_passed_total
        ),
        updated_at=record.updated_at.isoformat(),
    )


def _to_response(record: TenantWorkflowRecord) -> TenantWorkflowResponse:
    return TenantWorkflowResponse(
        id=record.id,
        account_id=record.account_id,
        slug=record.slug,
        label=record.label,
        description=record.description,
        enabled=record.enabled,
        sandbox_only=record.sandbox_only,
        priority=record.priority,
        search_hints=record.search_hints,
        importance=record.importance,
        required_fields=record.required_fields,
        optional_fields=record.optional_fields,
        extraction_schema=record.extraction_schema,
        classify_prompt=record.classify_prompt,
        extract_prompt=record.extract_prompt,
        draft_prompt=record.draft_prompt,
        few_shot_examples=[
            WorkflowFewShotExampleSchema(
                subject=item.subject,
                body=item.body,
                expected_json=item.expected_json,
            )
            for item in record.few_shot_examples
        ],
        test_emails=[
            WorkflowTestEmailSchema(
                subject=item.subject,
                body=item.body,
                expected_fields=item.expected_fields,
                attachments=list(item.attachments),
            )
            for item in record.test_emails
        ],
        match_rules=WorkflowMatchRulesSchema(
            subject_keywords=record.match_rules.subject_keywords,
            from_domains=record.match_rules.from_domains,
            body_keywords=record.match_rules.body_keywords,
        ),
        llm_provider=record.llm_provider,
        supports_multimodal=record.supports_multimodal,
        multimodal_prompt=record.multimodal_prompt,
        last_test_passed_at=(
            record.last_test_passed_at.isoformat()
            if record.last_test_passed_at
            else None
        ),
        last_test_passed_count=record.last_test_passed_count,
        last_test_passed_total=record.last_test_passed_total,
        created_by_user_id=record.created_by_user_id,
        updated_by_user_id=record.updated_by_user_id,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat(),
        version=record.version,
    )
