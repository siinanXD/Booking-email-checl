"""Mandanten-Workflows (Phase A — Sandbox, pro account_id)."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.roles import is_account_admin
from backend.api.middleware.tenant import get_request_account_id, require_account
from backend.api.schemas.tenant_workflows import (
    TenantWorkflowCreateRequest,
    TenantWorkflowPreviewRequest,
    TenantWorkflowSuggestRequest,
    TenantWorkflowUpdateRequest,
)
from backend.api.services.tenant_workflow_service import (
    create_workflow,
    delete_workflow,
    get_workflow,
    list_workflows,
    preview_workflow,
    run_workflow_tests,
    suggest_workflow,
    update_workflow,
)

workflows_bp = Blueprint("workflows", __name__, url_prefix="/api/workflows")


def _require_admin() -> tuple[Any, int] | None:
    role = g.current_user.get("role")
    if not is_account_admin(role):
        return jsonify({"error": "Admin required", "code": 403}), 403
    return None


def _account_id() -> str:
    account_id = get_request_account_id()
    assert account_id
    return account_id


@workflows_bp.get("")
@require_auth
@require_account
def tenant_list_workflows() -> tuple[Any, int]:
    data = list_workflows(g.ctx, _account_id())
    return jsonify(data.model_dump()), 200


@workflows_bp.post("")
@require_auth
@require_account
def tenant_create_workflow() -> tuple[Any, int]:
    denied = _require_admin()
    if denied:
        return denied
    body = TenantWorkflowCreateRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    user_id = g.current_user.get("id")
    try:
        created = create_workflow(
            g.ctx,
            _account_id(),
            body,
            user_id=user_id if isinstance(user_id, str) else None,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(created.model_dump()), 201


@workflows_bp.post("/suggest")
@require_auth
@require_account
def tenant_suggest_workflow() -> tuple[Any, int]:
    denied = _require_admin()
    if denied:
        return denied
    body = TenantWorkflowSuggestRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    suggestion = suggest_workflow(g.ctx, g.settings, body)
    return jsonify(suggestion.model_dump()), 200


@workflows_bp.get("/<workflow_id>")
@require_auth
@require_account
def tenant_get_workflow(workflow_id: str) -> tuple[Any, int]:
    record = get_workflow(g.ctx, _account_id(), workflow_id)
    if record is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record.model_dump()), 200


@workflows_bp.put("/<workflow_id>")
@require_auth
@require_account
def tenant_update_workflow(workflow_id: str) -> tuple[Any, int]:
    denied = _require_admin()
    if denied:
        return denied
    body = TenantWorkflowUpdateRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    user_id = g.current_user.get("id")
    try:
        updated = update_workflow(
            g.ctx,
            _account_id(),
            workflow_id,
            body,
            user_id=user_id if isinstance(user_id, str) else None,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409
    if updated is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(updated.model_dump()), 200


@workflows_bp.delete("/<workflow_id>")
@require_auth
@require_account
def tenant_delete_workflow(workflow_id: str) -> tuple[Any, int]:
    denied = _require_admin()
    if denied:
        return denied
    if not delete_workflow(g.ctx, _account_id(), workflow_id):
        return jsonify({"error": "Not found"}), 404
    return jsonify({"deleted": True}), 200


@workflows_bp.post("/<workflow_id>/preview")
@require_auth
@require_account
def tenant_preview_workflow(workflow_id: str) -> tuple[Any, int]:
    denied = _require_admin()
    if denied:
        return denied
    body = TenantWorkflowPreviewRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    result = preview_workflow(g.ctx, g.settings, _account_id(), workflow_id, body)
    if result is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result.model_dump()), 200


@workflows_bp.post("/<workflow_id>/run-tests")
@require_auth
@require_account
def tenant_run_workflow_tests(workflow_id: str) -> tuple[Any, int]:
    denied = _require_admin()
    if denied:
        return denied
    result = run_workflow_tests(g.ctx, g.settings, _account_id(), workflow_id)
    if result is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result.model_dump()), 200
