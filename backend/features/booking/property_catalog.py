"""Bekannte Unterkunftsnamen eines Mandanten (Properties + Empfänger)."""

from __future__ import annotations

from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.property_recipient_repository import (
    PropertyRecipientRepository,
)
from backend.infrastructure.repositories.property_repository import PropertyRepository


def known_property_names(db: Db, account_id: str) -> list[str]:
    """Alle konfigurierten Unterkunftsnamen für Abgleich mit Extraktionen."""
    names: set[str] = set()
    for row in PropertyRecipientRepository(db).list_all(account_id):
        if row.property_name.strip():
            names.add(row.property_name.strip())
    for prop in PropertyRepository(db).list_all(account_id=account_id):
        if prop.name.strip():
            names.add(prop.name.strip())
    return sorted(names, key=str.lower)
