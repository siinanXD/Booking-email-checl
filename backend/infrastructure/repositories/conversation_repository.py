"""Mail-Konversationen / Threads pro Mandant."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.infrastructure.repositories.domain_collections import CONVERSATIONS
from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter


class ConversationRecord(BaseModel):
    """Verknüpfte Nachrichten einer Konversation."""

    correlation_id: str
    message_ids: list[str] = Field(default_factory=list)
    account_id: str | None = None
    updated_at: str | None = None


class ConversationRepository:
    """Collection `conversations`."""

    COLLECTION = CONVERSATIONS

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]
        self._col.create_index([("account_id", 1), ("correlation_id", 1)])

    def upsert(
        self,
        record: ConversationRecord,
        *,
        account_id: str | None = None,
    ) -> ConversationRecord:
        """Konversation speichern oder aktualisieren."""
        resolved_account = account_id or record.account_id
        doc: dict[str, Any] = {
            "_id": record.correlation_id,
            "correlation_id": record.correlation_id,
            "message_ids": record.message_ids,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        if resolved_account:
            doc["account_id"] = resolved_account
        self._col.update_one({"_id": record.correlation_id}, {"$set": doc}, upsert=True)
        return record

    def get_by_correlation_id(
        self,
        correlation_id: str,
        *,
        account_id: str | None = None,
    ) -> ConversationRecord | None:
        """Lädt eine Konversation."""
        query = with_account_filter({"_id": correlation_id}, account_id)
        doc = self._col.find_one(query)
        if doc is None:
            return None
        payload = {k: v for k, v in doc.items() if k != "_id"}
        payload["correlation_id"] = str(doc["_id"])
        return ConversationRecord.model_validate(payload)
