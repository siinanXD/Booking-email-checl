"""Unterkünfte: Historie, Empfänger, Vorschläge."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.tenant import get_request_account_id, require_account
from backend.api.schemas.properties import PropertyRecipientsUpdateRequest
from backend.api.services.property_recipients_service import (
    get_recipients,
    save_recipients,
)
from backend.api.services.property_stats_queries import property_history
from backend.api.services.property_suggestions_queries import property_suggestions

properties_bp = Blueprint("properties", __name__, url_prefix="/api/properties")


@properties_bp.get("/history")
@require_auth
@require_account
def history() -> tuple[Any, int]:
    account_id = get_request_account_id()
    assert account_id
    limit = min(max(int(request.args.get("limit", 50)), 1), 100)
    prop = (request.args.get("property_name") or "").strip() or None
    result = property_history(g.ctx, account_id, property_name=prop, limit=limit)
    return jsonify(result.model_dump()), 200


@properties_bp.get("/recipients")
@require_auth
@require_account
def recipients_get() -> tuple[Any, int]:
    account_id = get_request_account_id()
    assert account_id
    return jsonify(get_recipients(g.ctx, account_id).model_dump()), 200


@properties_bp.put("/recipients")
@require_auth
@require_account
def recipients_put() -> tuple[Any, int]:
    account_id = get_request_account_id()
    assert account_id
    body = PropertyRecipientsUpdateRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    result = save_recipients(g.ctx, account_id, body.items)
    return jsonify(result.model_dump()), 200


@properties_bp.get("/suggestions")
@require_auth
@require_account
def suggestions() -> tuple[Any, int]:
    account_id = get_request_account_id()
    assert account_id
    limit = min(max(int(request.args.get("limit", 20)), 1), 50)
    result = property_suggestions(g.ctx, account_id, limit=limit)
    return jsonify(result.model_dump()), 200
