"""Persistenz von Review-Entwürfen und Freigabe-Status."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter


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
        account_id: str | None = None,
    ) -> ReviewRecord:
        """Speichert ausstehenden Review-Entwurf."""
        now = datetime.now(UTC)
        doc: dict[str, Any] = {
            "_id": correlation_id,
            "correlation_id": correlation_id,
            "message_id": message_id,
            "draft_body": draft_body,
            "grounding_flag": grounding_flag,
            "review_status": "pending",
            "intent": intent,
            "updated_at": now.isoformat(),
        }
        if account_id:
            doc["account_id"] = account_id
        self._col.update_one({"_id": correlation_id}, {"$set": doc}, upsert=True)
        return self.get(
            correlation_id, account_id=account_id
        ) or ReviewRecord.model_validate(doc)

    def update_status(
        self,
        correlation_id: str,
        status: str,
        *,
        account_id: str | None = None,
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
        query = with_account_filter({"_id": correlation_id}, account_id)
        self._col.update_one(query, {"$set": update})
        return self.get(correlation_id, account_id=account_id)

    def get(
        self,
        correlation_id: str,
        *,
        account_id: str | None = None,
    ) -> ReviewRecord | None:
        """Lädt einen Review-Datensatz."""
        query = with_account_filter({"_id": correlation_id}, account_id)
        doc = self._col.find_one(query)
        if doc is None:
            return None
        return ReviewRecord.model_validate(doc)

    def count_pending(self, *, account_id: str | None = None) -> int:
        """Anzahl ausstehender Reviews."""
        query = with_account_filter({"review_status": "pending"}, account_id)
        return int(self._col.count_documents(query))

    def list_pending(
        self,
        limit: int = 50,
        *,
        account_id: str | None = None,
    ) -> list[ReviewRecord]:
        """Ausstehende Reviews, neueste zuerst."""
        query = with_account_filter({"review_status": "pending"}, account_id)
        cursor = self._col.find(query).sort("updated_at", -1).limit(limit)
        return [ReviewRecord.model_validate(doc) for doc in cursor]
