"""Text-Chunks pro Mail (mandantenscharf, getrennt von Vektoren)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.collection import Collection

from backend.infrastructure.repositories.domain_collections import CHUNKS
from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter


class ChunkRepository:
    """Collection `chunks` — Rohtext-Segmente für Indexierung."""

    COLLECTION = CHUNKS

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]
        self._col.create_index([("account_id", 1), ("correlation_id", 1)])

    def upsert_chunk(
        self,
        chunk_id: str,
        correlation_id: str,
        text: str,
        intent: str | None = None,
        *,
        account_id: str | None = None,
    ) -> None:
        """Speichert einen Text-Chunk."""
        doc: dict[str, Any] = {
            "_id": chunk_id,
            "correlation_id": correlation_id,
            "text": text,
            "intent": intent,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        if account_id:
            doc["account_id"] = account_id
        self._col.update_one({"_id": chunk_id}, {"$set": doc}, upsert=True)

    def list_by_correlation_id(
        self,
        correlation_id: str,
        *,
        account_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lädt alle Chunks einer Mail-Korrelation."""
        query = with_account_filter({"correlation_id": correlation_id}, account_id)
        return list(self._col.find(query))
