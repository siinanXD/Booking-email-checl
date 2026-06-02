"""Kurzlebige MSAL Auth-Code-Flows für Outlook OAuth."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db

FLOW_TTL = timedelta(minutes=15)


class OutlookOAuthFlowRecord(BaseModel):
    """Pending OAuth state zwischen Authorize und Callback."""

    state: str
    account_id: str
    flow: dict[str, Any]
    return_to: str = "/onboarding"
    frontend_origin: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OutlookOAuthFlowRepository:
    """Collection `outlook_oauth_flows` – TTL über created_at beim Lesen."""

    COLLECTION = "outlook_oauth_flows"

    def __init__(self, db: Db) -> None:
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def save(self, record: OutlookOAuthFlowRecord) -> None:
        doc = record.model_dump(mode="json")
        doc["_id"] = record.state
        self._col.replace_one({"_id": record.state}, doc, upsert=True)

    def pop(self, state: str) -> OutlookOAuthFlowRecord | None:
        """Lädt und löscht Flow (einmalig)."""
        doc = self._col.find_one_and_delete({"_id": state})
        if doc is None:
            return None
        payload = {k: v for k, v in doc.items() if k != "_id"}
        payload["state"] = state
        record = OutlookOAuthFlowRecord.model_validate(payload)
        if record.created_at < datetime.now(UTC) - FLOW_TTL:
            return None
        return record
