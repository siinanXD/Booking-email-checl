"""Persistenz eingegangener E-Mails."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.collection import Collection

from models.email import ProcessingState, StoredEmail
from repositories.mongo import Db


class EmailRepository:
    """CRUD für die Collection `emails`."""

    COLLECTION = "emails"

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def upsert_by_message_id(self, email: StoredEmail) -> StoredEmail:
        """Idempotentes Speichern nach Message-ID."""
        now = datetime.now(UTC)
        doc = email.to_mongo()
        doc["updated_at"] = now.isoformat()
        if email.created_at is None:
            doc["created_at"] = now.isoformat()
        self._col.update_one(
            {"_id": email.message_id},
            {"$set": doc},
            upsert=True,
        )
        stored = self.get_by_message_id(email.message_id)
        if stored is None:
            msg = f"Upsert failed for message_id={email.message_id}"
            raise RuntimeError(msg)
        return stored

    def get_by_message_id(self, message_id: str) -> StoredEmail | None:
        """Lädt eine Mail anhand der Message-ID."""
        doc = self._col.find_one({"_id": message_id})
        if doc is None:
            doc = self._col.find_one({"message_id": message_id})
        if doc is None:
            return None
        return StoredEmail.from_mongo(doc)

    def update_processing_state(
        self,
        message_id: str,
        state: ProcessingState,
        **extra: Any,
    ) -> StoredEmail | None:
        """Aktualisiert Verarbeitungsstatus und optionale Felder."""
        update: dict[str, Any] = {
            "processing_state": state.value,
            "updated_at": datetime.now(UTC).isoformat(),
            **extra,
        }
        self._col.update_one({"_id": message_id}, {"$set": update})
        return self.get_by_message_id(message_id)

    def list_by_correlation_id(self, correlation_id: str) -> list[StoredEmail]:
        """Alle Mails einer Correlation-ID."""
        cursor = self._col.find({"correlation_id": correlation_id})
        return [StoredEmail.from_mongo(doc) for doc in cursor]

    def get_by_correlation_id(self, correlation_id: str) -> StoredEmail | None:
        """Erste Mail zu einer Correlation-ID."""
        doc = self._col.find_one({"correlation_id": correlation_id})
        if doc is None:
            return None
        return StoredEmail.from_mongo(doc)

    def list_filtered(
        self,
        *,
        status: str | None = None,
        intent: str | None = None,
        platform: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[StoredEmail], int]:
        """Paginierte Liste mit optionalen Filtern."""
        base_match: dict[str, Any] = {}
        if status:
            base_match["processing_state"] = status
        if platform:
            base_match["platform"] = platform
        if search:
            base_match["$or"] = [
                {"subject": {"$regex": search, "$options": "i"}},
                {"from_address": {"$regex": search, "$options": "i"}},
                {"correlation_id": search},
            ]

        skip = max(page - 1, 0) * limit
        if intent:
            match_stage = {**base_match, "ext.extraction.intent": intent}
            pipeline: list[dict[str, Any]] = [
                {
                    "$lookup": {
                        "from": "extractions",
                        "localField": "correlation_id",
                        "foreignField": "_id",
                        "as": "ext",
                    }
                },
                {"$unwind": {"path": "$ext", "preserveNullAndEmptyArrays": False}},
                {"$match": match_stage},
                {"$sort": {"updated_at": -1}},
                {
                    "$facet": {
                        "items": [{"$skip": skip}, {"$limit": limit}],
                        "total": [{"$count": "count"}],
                    }
                },
            ]
            agg = list(self._col.aggregate(pipeline))
            if not agg:
                return [], 0
            items_raw = agg[0].get("items", [])
            total_arr = agg[0].get("total", [])
            total = int(total_arr[0]["count"]) if total_arr else 0
            return [StoredEmail.from_mongo(doc) for doc in items_raw], total

        total = int(self._col.count_documents(base_match))
        cursor = (
            self._col.find(base_match).sort("updated_at", -1).skip(skip).limit(limit)
        )
        return [StoredEmail.from_mongo(doc) for doc in cursor], total

    def count_by_state_since(
        self,
        state: ProcessingState,
        since_iso: str,
    ) -> int:
        """Zählt Mails mit Status seit Zeitstempel (ISO)."""
        return int(
            self._col.count_documents(
                {
                    "processing_state": state.value,
                    "updated_at": {"$gte": since_iso},
                }
            )
        )

    def count_updated_since(self, since_iso: str) -> int:
        """Alle Mails mit Update seit Zeitstempel."""
        return int(self._col.count_documents({"updated_at": {"$gte": since_iso}}))
