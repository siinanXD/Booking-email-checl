"""Weist bestehenden Betriebsdaten einen Account zu (Phase-2-Migration)."""

from __future__ import annotations

import sys
from pathlib import Path

TENANT_COLLECTIONS = (
    "emails",
    "extractions",
    "reviews",
    "embeddings",
    "chunks",
    "mail_metrics",
    "notification_outbox",
    "property_whatsapp_recipients",
    "guests",
    "bookings",
    "properties",
    "conversations",
)


def main() -> int:
    """Ordnet Daten ohne account_id dem Plattform-Admin-Account zu."""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from backend.core.config.settings import get_settings
    from backend.infrastructure.repositories.mongo import get_database
    from backend.infrastructure.repositories.platform_settings_repository import (
        LEGACY_PLATFORM_DOC_ID,
    )
    from backend.infrastructure.repositories.user_repository import UserRepository

    settings = get_settings()
    db = get_database(settings)
    users = UserRepository(db)
    admin = users.get_by_email(settings.admin_email)
    if admin is None or not admin.account_id:
        print("Kein Plattform-Admin mit account_id gefunden – Seed zuerst ausführen.")
        return 1

    account_id = admin.account_id
    print(f"Migriere Daten → account_id={account_id}")

    for name in TENANT_COLLECTIONS:
        result = db[name].update_many(
            {"account_id": {"$exists": False}},
            {"$set": {"account_id": account_id}},
        )
        print(f"  {name}: {result.modified_count} Dokument(e)")

    legacy = db["platform_settings"].find_one({"_id": LEGACY_PLATFORM_DOC_ID})
    if legacy is not None and not db["platform_settings"].find_one({"_id": account_id}):
        migrated = {k: v for k, v in legacy.items() if k != "_id"}
        migrated["_id"] = account_id
        migrated["id"] = account_id
        migrated["account_id"] = account_id
        db["platform_settings"].insert_one(migrated)
        print("  platform_settings: Legacy-Dokument kopiert")

    props = db["property_whatsapp_recipients"].find(
        {"account_id": account_id, "_id": {"$not": {"$regex": "^" + account_id + ":"}}}
    )
    for doc in props:
        old_id = doc["_id"]
        prop_key = doc.get("property_name_lower") or str(old_id)
        new_id = f"{account_id}:{prop_key}"
        if old_id == new_id:
            continue
        doc["_id"] = new_id
        db["property_whatsapp_recipients"].insert_one(doc)
        db["property_whatsapp_recipients"].delete_one({"_id": old_id})
    print("Migration abgeschlossen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
