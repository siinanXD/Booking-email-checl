"""Human-Review-API."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from web.middleware.auth_guard import require_auth
from web.middleware.tenant import get_request_account_id, require_account
from web.schemas.review import (
    ReviewApproveRequest,
    ReviewQueueResponse,
    ReviewRejectRequest,
)
from web.services.api_helpers import tenant_query_service

review_bp = Blueprint("review", __name__, url_prefix="/api/review")


def _assert_tenant_owns_correlation(correlation_id: str) -> tuple[Any, int] | None:
    account_id = get_request_account_id()
    if not account_id:
        return jsonify({"error": "Account context required", "code": 403}), 403
    email = g.ctx.email_repo.get_by_correlation_id(
        correlation_id,
        account_id=account_id,
    )
    if email is None:
        return jsonify({"error": "Email not found", "code": 404}), 404
    return None


@review_bp.get("/pending")
@require_auth
@require_account
def list_pending() -> tuple[Any, int]:
    """Ausstehende Entwürfe inkl. LLM-Antworttext."""
    limit = min(max(int(request.args.get("limit", 50)), 1), 100)
    svc = tenant_query_service()
    items = svc.list_review_pending(limit=limit)
    return (
        jsonify(ReviewQueueResponse(items=items, total=len(items)).model_dump()),
        200,
    )


@review_bp.post("/approve")
@require_auth
@require_account
def approve() -> tuple[Any, int]:
    """Freigabe eines Entwurfs (kein Auto-Versand)."""
    body = ReviewApproveRequest.model_validate(request.get_json(silent=True) or {})
    denied = _assert_tenant_owns_correlation(body.correlation_id)
    if denied:
        return denied
    try:
        result = g.ctx.review_router.approve_draft(
            body.correlation_id,
            approved_body=body.approved_body,
        )
    except Exception as exc:
        return jsonify({"error": str(exc), "code": 400}), 400
    return jsonify({"status": "approved", "result_keys": list(result.keys())}), 200


@review_bp.post("/reject")
@require_auth
@require_account
def reject() -> tuple[Any, int]:
    """Ablehnung eines Entwurfs."""
    body = ReviewRejectRequest.model_validate(request.get_json(silent=True) or {})
    denied = _assert_tenant_owns_correlation(body.correlation_id)
    if denied:
        return denied
    try:
        result = g.ctx.review_router.reject_draft(
            body.correlation_id,
            reason=body.reason or None,
        )
    except Exception as exc:
        return jsonify({"error": str(exc), "code": 400}), 400
    return jsonify({"status": "rejected", "result_keys": list(result.keys())}), 200
