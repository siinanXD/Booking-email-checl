"""Postfach-Verbindung API."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.roles import is_account_admin
from backend.api.middleware.tenant import get_request_account_id, require_account
from backend.api.schemas.mail import MailConnectionUpdate, MailTestResponse
from backend.features.mail.mail_connection_service import MailConnectionService

mail_bp = Blueprint("mail", __name__, url_prefix="/api/mail")


def _require_admin() -> tuple[Any, int] | None:
    role = g.current_user.get("role")
    if not is_account_admin(role):
        return jsonify({"error": "Admin required", "code": 403}), 403
    return None


def _service() -> MailConnectionService:
    return MailConnectionService(
        g.ctx.mail_connection_repo,
        g.ctx.platform_settings_repo,
        g.settings,
    )


@mail_bp.get("/connection")
@require_auth
@require_account
def get_connection() -> tuple[Any, int]:
    """Lädt Postfach-Konfiguration des Accounts."""
    denied = _require_admin()
    if denied:
        return denied
    account_id = get_request_account_id()
    assert account_id
    return jsonify(_service().get_response(account_id).model_dump()), 200


@mail_bp.put("/connection")
@require_auth
@require_account
def update_connection() -> tuple[Any, int]:
    """Speichert Postfach-Konfiguration."""
    denied = _require_admin()
    if denied:
        return denied
    account_id = get_request_account_id()
    assert account_id
    body = MailConnectionUpdate.model_validate(request.get_json(silent=True) or {})
    response = _service().apply_update(account_id, body)
    return jsonify(response.model_dump()), 200


@mail_bp.post("/test")
@require_auth
@require_account
def test_connection() -> tuple[Any, int]:
    """Testet die gespeicherte Postfach-Verbindung."""
    denied = _require_admin()
    if denied:
        return denied
    account_id = get_request_account_id()
    assert account_id
    result = _service().test_connection(account_id)
    status = 200 if result.success else 502
    return (
        jsonify(
            MailTestResponse(
                success=result.success,
                message=result.message,
                mailbox_count=result.mailbox_count,
            ).model_dump()
        ),
        status,
    )
