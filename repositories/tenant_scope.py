"""Hilfen für mandantenspezifische MongoDB-Filter."""

from __future__ import annotations

from typing import Any


def with_account_filter(
    base: dict[str, Any],
    account_id: str | None,
) -> dict[str, Any]:
    """Fügt account_id zum Filter hinzu, wenn gesetzt."""
    if not account_id:
        return base
    if not base:
        return {"account_id": account_id}
    return {"$and": [base, {"account_id": account_id}]}
