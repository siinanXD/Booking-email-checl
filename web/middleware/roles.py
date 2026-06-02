"""Rollen-Hilfen für API-Middleware."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from flask import g, jsonify

F = TypeVar("F", bound=Callable[..., Any])

ACCOUNT_ADMIN_ROLES = frozenset({"owner", "admin", "platform_admin"})


def is_platform_admin(role: str | None) -> bool:
    """Prüft Plattform-Admin-Rolle."""
    return role == "platform_admin"


def is_account_admin(role: str | None) -> bool:
    """Prüft Account-Admin-Berechtigung (Einstellungen etc.)."""
    return role in ACCOUNT_ADMIN_ROLES


def require_platform_admin(fn: F) -> F:
    """Decorator: nur Plattform-Admin."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        role = g.current_user.get("role")
        if not is_platform_admin(role):
            return jsonify({"error": "Platform admin required", "code": 403}), 403
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
