"""Tenant-Kontext für API-Anfragen."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from flask import g, jsonify

F = TypeVar("F", bound=Callable[..., Any])


def get_request_account_id() -> str | None:
    """account_id aus JWT-Kontext."""
    return getattr(g, "current_account_id", None)


def require_account(fn: F) -> F:
    """Decorator: erfordert account_id im JWT (nach require_auth)."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        account_id = get_request_account_id()
        if not account_id:
            return (
                jsonify({"error": "Account context required", "code": 403}),
                403,
            )
        g.tenant_account_id = account_id
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
