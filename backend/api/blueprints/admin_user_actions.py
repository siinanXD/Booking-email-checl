"""Plattform-Admin: Passwort-Reset, Sperren, Löschen, Ablaufdatum."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from flask import g, jsonify, request
from werkzeug.security import generate_password_hash

from backend.api.blueprints.admin import admin_bp
from backend.api.middleware.auth_guard import require_auth
from backend.api.middleware.roles import require_platform_admin
from backend.api.schemas.accounts import (
    AccountExpiryRequest,
    UserLockRequest,
    UserResetPasswordRequest,
)


def _account_or_404(account_id: str) -> Any | None:
    return g.ctx.account_repo.get_by_id(account_id)


def _user_or_404(user_id: str, account_id: str) -> Any | None:
    user = g.ctx.user_repo.get_by_id(user_id)
    if user is None or user.account_id != account_id:
        return None
    return user


# ── Account: Ablaufdatum ──────────────────────────────────────────────────


@admin_bp.post("/accounts/<account_id>/expiry")
@require_auth
@require_platform_admin
def set_account_expiry(account_id: str) -> tuple[Any, int]:
    """Setzt oder entfernt ein Ablaufdatum für einen Mandanten."""
    if _account_or_404(account_id) is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    body = AccountExpiryRequest.model_validate(request.get_json(silent=True) or {})
    expires_at: datetime | None = None
    if body.expires_at:
        try:
            expires_at = datetime.fromisoformat(body.expires_at).astimezone(UTC)
        except ValueError:
            return jsonify({"error": "Ungültiges Datumsformat", "code": 400}), 400
    g.ctx.account_repo.set_expiry(account_id, expires_at)
    exp_iso = expires_at.isoformat() if expires_at else None
    msg = f"Ablaufdatum: {exp_iso}" if expires_at else "Ablaufdatum entfernt."
    return jsonify({"id": account_id, "expires_at": exp_iso, "message": msg}), 200


# ── Account: Sperren / Entsperren ────────────────────────────────────────


@admin_bp.post("/accounts/<account_id>/suspend")
@require_auth
@require_platform_admin
def suspend_account(account_id: str) -> tuple[Any, int]:
    """Sperrt einen Mandanten (status → suspended)."""
    if _account_or_404(account_id) is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    g.ctx.account_repo.update_status(account_id, "suspended")
    return jsonify({"id": account_id, "status": "suspended"}), 200


@admin_bp.post("/accounts/<account_id>/unsuspend")
@require_auth
@require_platform_admin
def unsuspend_account(account_id: str) -> tuple[Any, int]:
    """Entsperrt einen Mandanten (status → active)."""
    if _account_or_404(account_id) is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    g.ctx.account_repo.update_status(account_id, "active")
    return jsonify({"id": account_id, "status": "active"}), 200


# ── Account: Löschen ──────────────────────────────────────────────────────


@admin_bp.delete("/accounts/<account_id>")
@require_auth
@require_platform_admin
def delete_account(account_id: str) -> tuple[Any, int]:
    """Löscht einen Mandanten und alle seine Benutzer (unwiderruflich)."""
    if _account_or_404(account_id) is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    for user in g.ctx.user_repo.list_by_account_id(account_id):
        g.ctx.user_repo.delete(user.id)
    g.ctx.account_repo.delete(account_id)
    return jsonify({"id": account_id, "message": "Mandant gelöscht."}), 200


# ── User: Sperren / Entsperren ───────────────────────────────────────────


@admin_bp.post("/accounts/<account_id>/users/<user_id>/lock")
@require_auth
@require_platform_admin
def lock_user(account_id: str, user_id: str) -> tuple[Any, int]:
    """Sperrt oder entsperrt einen einzelnen Benutzer."""
    if _user_or_404(user_id, account_id) is None:
        return jsonify({"error": "User not found", "code": 404}), 404
    body = UserLockRequest.model_validate(
        request.get_json(silent=True) or {"locked": True}
    )
    g.ctx.user_repo.set_locked(user_id, body.locked)
    state = "gesperrt" if body.locked else "entsperrt"
    return jsonify({"id": user_id, "is_locked": body.locked, "message": state}), 200


# ── User: Passwort zurücksetzen ───────────────────────────────────────────


@admin_bp.post("/accounts/<account_id>/users/<user_id>/reset-password")
@require_auth
@require_platform_admin
def reset_user_password(account_id: str, user_id: str) -> tuple[Any, int]:
    """Setzt das Passwort eines Benutzers zurück."""
    if _user_or_404(user_id, account_id) is None:
        return jsonify({"error": "User not found", "code": 404}), 404
    body = UserResetPasswordRequest.model_validate(request.get_json(silent=True) or {})
    new_hash = generate_password_hash(body.new_password)
    g.ctx.user_repo.reset_password_hash(user_id, new_hash)
    return jsonify({"id": user_id, "message": "Passwort zurückgesetzt."}), 200


# ── User: Löschen ─────────────────────────────────────────────────────────


@admin_bp.delete("/accounts/<account_id>/users/<user_id>")
@require_auth
@require_platform_admin
def delete_user(account_id: str, user_id: str) -> tuple[Any, int]:
    """Löscht einen einzelnen Benutzer eines Mandanten."""
    if _user_or_404(user_id, account_id) is None:
        return jsonify({"error": "User not found", "code": 404}), 404
    g.ctx.user_repo.delete(user_id)
    return jsonify({"id": user_id, "message": "Benutzer gelöscht."}), 200
