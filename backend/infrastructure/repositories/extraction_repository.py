"""Persistenz von Extraktionen."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.collection import Collection

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter


class ExtractionRepository:
    """Collection `extractions`."""

    COLLECTION = "extractions"

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def save(
        self,
        correlation_id: str,
        message_id: str,
        extraction: BookingExtraction,
        *,
        account_id: str | None = None,
    ) -> None:
        """Extraktion speichern."""
        doc: dict[str, Any] = {
            "_id": correlation_id,
            "message_id": message_id,
            "extraction": extraction.model_dump(mode="json"),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        if account_id:
            doc["account_id"] = account_id
        self._col.update_one({"_id": correlation_id}, {"$set": doc}, upsert=True)

    def get_by_correlation_id(
        self,
        correlation_id: str,
        *,
        account_id: str | None = None,
    ) -> BookingExtraction | None:
        """Extraktion laden."""
        query = with_account_filter({"_id": correlation_id}, account_id)
        doc = self._col.find_one(query)
        if doc is None and account_id:
            doc = self._col.find_one({"_id": correlation_id})
            if doc and doc.get("account_id") not in (None, account_id):
                return None
        if doc is None or "extraction" not in doc:
            return None
        return BookingExtraction.model_validate(doc["extraction"])
