"""Unterkunftsnamen eines Mandanten."""

from __future__ import annotations

from backend.core.config.factory import AppContext
from backend.features.booking.property_catalog import known_property_names


def list_property_names(ctx: AppContext, account_id: str) -> list[str]:
    """Alle bekannten Unterkunftsnamen (Empfänger + Properties-Collection)."""
    return known_property_names(ctx.db, account_id)
