"""Plattform-Admin: Mandanten-Workflows."""

from __future__ import annotations

from typing import Any

from flask import g, jsonify, request

from backend.api.blueprints.admin import admin_bp
from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.roles import require_platform_admin


def _account_or_404(account_id: str) -> tuple[Any, int] | None:
    if g.ctx.account_repo.get_by_id(account_id) is None:
        return jsonify({"error": "Account not found"}), 404
    return None


@admin_bp.get("/accounts/<account_id>/workflows/gemini-status")
@require_auth
@require_platform_admin
def admin_gemini_status(account_id: str) -> tuple[Any, int]:
    """Gemini-Konfiguration (global, kein Key-Leak)."""
    _ = account_id
    from backend.api.services.tenant_workflow_service import gemini_status

    return jsonify(gemini_status(g.settings, g.ctx).model_dump()), 200


@admin_bp.get("/accounts/<account_id>/workflows")
@require_auth
@require_platform_admin
def admin_list_account_workflows(account_id: str) -> tuple[Any, int]:
    """Workflows eines Mandanten (Plattform-Admin)."""
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.api.services.tenant_workflow_service import list_workflows

    return jsonify(list_workflows(g.ctx, account_id).model_dump()), 200


@admin_bp.post("/accounts/<account_id>/workflows")
@require_auth
@require_platform_admin
def admin_create_account_workflow(account_id: str) -> tuple[Any, int]:
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.api.schemas.tenant_workflows import TenantWorkflowCreateRequest
    from backend.api.services.tenant_workflow_service import create_workflow

    body = TenantWorkflowCreateRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    user_id = g.current_user.get("id")
    try:
        created = create_workflow(
            g.ctx,
            account_id,
            body,
            user_id=user_id if isinstance(user_id, str) else None,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(created.model_dump()), 201


@admin_bp.post("/accounts/<account_id>/workflows/suggest")
@require_auth
@require_platform_admin
def admin_suggest_account_workflow(account_id: str) -> tuple[Any, int]:
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.ai.services.tenant_workflow_suggest_gemini import (
        SuggestRequiresGeminiError,
    )
    from backend.api.schemas.tenant_workflows import TenantWorkflowSuggestRequest
    from backend.api.services.tenant_workflow_service import suggest_workflow

    try:
        body = TenantWorkflowSuggestRequest.model_validate(
            request.get_json(silent=True) or {}
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    try:
        suggestion = suggest_workflow(g.ctx, g.settings, body)
    except SuggestRequiresGeminiError as exc:
        return jsonify({"error": str(exc), "code": "gemini_required"}), 503
    return jsonify(suggestion.model_dump()), 200


@admin_bp.get("/accounts/<account_id>/workflows/<workflow_id>")
@require_auth
@require_platform_admin
def admin_get_account_workflow(
    account_id: str,
    workflow_id: str,
) -> tuple[Any, int]:
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.api.services.tenant_workflow_service import get_workflow

    record = get_workflow(g.ctx, account_id, workflow_id)
    if record is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record.model_dump()), 200


@admin_bp.put("/accounts/<account_id>/workflows/<workflow_id>")
@require_auth
@require_platform_admin
def admin_update_account_workflow(
    account_id: str,
    workflow_id: str,
) -> tuple[Any, int]:
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.api.schemas.tenant_workflows import TenantWorkflowUpdateRequest
    from backend.api.services.tenant_workflow_service import update_workflow

    body = TenantWorkflowUpdateRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    user_id = g.current_user.get("id")
    try:
        updated = update_workflow(
            g.ctx,
            account_id,
            workflow_id,
            body,
            user_id=user_id if isinstance(user_id, str) else None,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409
    if updated is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(updated.model_dump()), 200


@admin_bp.delete("/accounts/<account_id>/workflows/<workflow_id>")
@require_auth
@require_platform_admin
def admin_delete_account_workflow(
    account_id: str,
    workflow_id: str,
) -> tuple[Any, int]:
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.api.services.tenant_workflow_service import delete_workflow

    if not delete_workflow(g.ctx, account_id, workflow_id):
        return jsonify({"error": "Not found"}), 404
    return jsonify({"deleted": True}), 200


@admin_bp.post("/accounts/<account_id>/workflows/<workflow_id>/preview")
@require_auth
@require_platform_admin
def admin_preview_account_workflow(
    account_id: str,
    workflow_id: str,
) -> tuple[Any, int]:
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.api.schemas.tenant_workflows import TenantWorkflowPreviewRequest
    from backend.api.services.tenant_workflow_service import preview_workflow

    body = TenantWorkflowPreviewRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    result = preview_workflow(g.ctx, g.settings, account_id, workflow_id, body)
    if result is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result.model_dump()), 200


@admin_bp.post("/accounts/<account_id>/workflows/<workflow_id>/run-tests")
@require_auth
@require_platform_admin
def admin_run_account_workflow_tests(
    account_id: str,
    workflow_id: str,
) -> tuple[Any, int]:
    missing = _account_or_404(account_id)
    if missing:
        return missing
    from backend.api.services.tenant_workflow_service import run_workflow_tests

    result = run_workflow_tests(g.ctx, g.settings, account_id, workflow_id)
    if result is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result.model_dump()), 200
