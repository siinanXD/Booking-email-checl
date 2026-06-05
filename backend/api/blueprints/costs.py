"""API-Kosten-Endpoints."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.roles import require_platform_admin
from backend.api.services import dashboard_queries

costs_bp = Blueprint("costs", __name__, url_prefix="/api/costs")


@costs_bp.get("/")
@require_auth
@require_platform_admin
def costs() -> tuple[Any, int]:
    """Plattformweite Kosten-Aggregation (nur Plattform-Admin)."""
    result = dashboard_queries.costs(
        g.ctx,
        None,
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
        group_by=request.args.get("group_by", "day"),
    )
    return jsonify(result.model_dump()), 200
