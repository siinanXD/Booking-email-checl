"""API-Kosten-Endpoints."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.tenant import require_account
from backend.api.services.api_helpers import tenant_query_service

costs_bp = Blueprint("costs", __name__, url_prefix="/api/costs")


@costs_bp.get("/")
@require_auth
@require_account
def costs() -> tuple[Any, int]:
    """Kosten-Aggregation."""
    svc = tenant_query_service()
    result = svc.costs(
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
        group_by=request.args.get("group_by", "day"),
    )
    return jsonify(result.model_dump()), 200
