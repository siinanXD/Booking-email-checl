"""Plattform-Admin: globale LLM-Konfiguration."""

from __future__ import annotations

from typing import Any, cast

from flask import g, jsonify, request

from backend.api.blueprints.admin import admin_bp
from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.roles import require_platform_admin
from backend.api.schemas.admin_llm_config import (
    AdminLlmConfigUpdateRequest,
    AdminLlmPreviewRequest,
    LlmPromptType,
)
from backend.api.services.admin_llm_config_service import (
    get_llm_config,
    get_prompt_history,
    preview_llm_config,
    update_llm_config,
)


@admin_bp.get("/llm-config")
@require_auth
@require_platform_admin
def admin_get_llm_config() -> tuple[Any, int]:
    """Globale LLM-/Prompt-Konfiguration."""
    return jsonify(get_llm_config(g.ctx).model_dump()), 200


@admin_bp.put("/llm-config")
@require_auth
@require_platform_admin
def admin_put_llm_config() -> tuple[Any, int]:
    """Speichert LLM-/Prompt-Konfiguration."""
    body = AdminLlmConfigUpdateRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    user_id = g.current_user.get("id")
    updated = update_llm_config(
        g.ctx,
        body,
        user_id=user_id if isinstance(user_id, str) else None,
    )
    return jsonify(updated.model_dump()), 200


@admin_bp.post("/llm-config/preview")
@require_auth
@require_platform_admin
def admin_preview_llm_config() -> tuple[Any, int]:
    """Dry-Run classify/extract auf Beispieltext."""
    body = AdminLlmPreviewRequest.model_validate(request.get_json(silent=True) or {})
    result = preview_llm_config(g.ctx, g.settings, body)
    return jsonify(result.model_dump()), 200


@admin_bp.get("/llm-config/prompt-history/<prompt_type>")
@require_auth
@require_platform_admin
def admin_llm_prompt_history(prompt_type: str) -> tuple[Any, int]:
    """Letzte gespeicherte Prompt-Versionen für classify/extract/draft."""
    if prompt_type not in {"classify", "extract", "draft"}:
        return jsonify({"error": "invalid prompt_type"}), 400
    limit = request.args.get("limit", default=15, type=int)
    result = get_prompt_history(
        g.ctx,
        cast(LlmPromptType, prompt_type),
        limit=limit,
    )
    return jsonify(result.model_dump()), 200
