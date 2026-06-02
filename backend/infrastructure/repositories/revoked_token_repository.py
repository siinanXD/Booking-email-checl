"""Persistierte JWT-Blocklist (worker-übergreifend via MongoDB)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db


class RevokedTokenRepository:
    """Collection `revoked_tokens` mit TTL auf abgelaufene Einträge."""

    COLLECTION = "revoked_tokens"

    def __init__(self, db: Db) -> None:
        """Initialisiert Collection und TTL-Index."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """TTL-Index: Dokumente werden nach `expires_at` automatisch gelöscht."""
        self._col.create_index("expires_at", expireAfterSeconds=0)

    def revoke(self, jti: str, *, expires_at: datetime | None = None) -> None:
        """Speichert widerrufenes JTI (idempotent)."""
        doc: dict[str, Any] = {
            "_id": jti,
            "revoked_at": datetime.now(UTC),
        }
        if expires_at is not None:
            doc["expires_at"] = expires_at
        self._col.update_one({"_id": jti}, {"$set": doc}, upsert=True)

    def is_revoked(self, jti: str) -> bool:
        """Prüft ob JTI in der Blocklist steht."""
        return self._col.find_one({"_id": jti}) is not None

    def clear_all(self) -> None:
        """Leert die Collection (nur Tests)."""
        self._col.delete_many({})
