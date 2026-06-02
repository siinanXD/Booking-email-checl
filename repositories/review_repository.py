"""Persistenz von Review-Entwürfen und Freigabe-Status."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from repositories.mongo import Db


class ReviewRecord(BaseModel):
    """Gespeicherter Review-Stand für die Web-API."""

    correlation_id: str
    message_id: str
    draft_body: str = ""
    grounding_flag: bool = False
    review_status: str = "pending"
    reviewer_note: str | None = None
    approved_body: str | None = None
    intent: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReviewRepository:
    """Collection `reviews`."""

    COLLECTION = "reviews"

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def upsert_pending(
        self,
        *,
        correlation_id: str,
        message_id: str,
        draft_body: str,
        grounding_flag: bool,
        intent: str | None,
    ) -> ReviewRecord:
        """Speichert ausstehenden Review-Entwurf."""
        now = datetime.now(UTC)
        doc = {
            "_id": correlation_id,
            "correlation_id": correlation_id,
            "message_id": message_id,
            "draft_body": draft_body,
            "grounding_flag": grounding_flag,
            "review_status": "pending",
            "intent": intent,
            "updated_at": now.isoformat(),
        }
        self._col.update_one({"_id": correlation_id}, {"$set": doc}, upsert=True)
        return self.get(correlation_id) or ReviewRecord.model_validate(doc)

    def update_status(
        self,
        correlation_id: str,
        status: str,
        *,
        approved_body: str | None = None,
        reviewer_note: str | None = None,
    ) -> ReviewRecord | None:
        """Aktualisiert Review-Status nach Freigabe/Ablehnung."""
        update: dict[str, Any] = {
            "review_status": status,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        if approved_body is not None:
            update["approved_body"] = approved_body
        if reviewer_note is not None:
            update["reviewer_note"] = reviewer_note
        self._col.update_one({"_id": correlation_id}, {"$set": update})
        return self.get(correlation_id)

    def get(self, correlation_id: str) -> ReviewRecord | None:
        """Lädt einen Review-Datensatz."""
        doc = self._col.find_one({"_id": correlation_id})
        if doc is None:
            return None
        return ReviewRecord.model_validate(doc)

    def count_pending(self) -> int:
        """Anzahl ausstehender Reviews."""
        return int(self._col.count_documents({"review_status": "pending"}))

    def list_pending(self, limit: int = 50) -> list[ReviewRecord]:
        """Ausstehende Reviews, neueste zuerst."""
        cursor = (
            self._col.find({"review_status": "pending"})
            .sort("updated_at", -1)
            .limit(limit)
        )
        return [ReviewRecord.model_validate(doc) for doc in cursor]
