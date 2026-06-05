"""Vom Review gelernte Klassifikations-Beispiele pro Mandant."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter

_MAX_PER_ACCOUNT = 15


class TenantLearnedExamplesRepository:
    """Collection `tenant_classify_examples`."""

    COLLECTION = "tenant_classify_examples"

    def __init__(self, db: Db) -> None:
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def add_classify_example(
        self,
        account_id: str,
        *,
        subject: str,
        body: str,
        intent: str,
        correlation_id: str,
    ) -> None:
        """Speichert ein freigegebenes Mail-Beispiel (neueste zuerst, begrenzt)."""
        now = datetime.now(UTC).isoformat()
        doc_id = f"{account_id}:{correlation_id}"
        self._col.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "account_id": account_id,
                    "subject": subject[:200],
                    "body": body[:800],
                    "intent": intent,
                    "correlation_id": correlation_id,
                    "learned_at": now,
                }
            },
            upsert=True,
        )
        self._trim_old(account_id)

    def list_recent(
        self,
        account_id: str,
        *,
        limit: int = 5,
    ) -> list[dict[str, object]]:
        """Neueste Beispiele für Few-Shot-Prompts."""
        query = with_account_filter({}, account_id)
        cursor = self._col.find(query).sort("learned_at", -1).limit(limit)
        return [
            {
                "subject": doc.get("subject", ""),
                "body": doc.get("body", ""),
                "intent": doc.get("intent", "other"),
            }
            for doc in cursor
        ]

    def _trim_old(self, account_id: str) -> None:
        query = with_account_filter({}, account_id)
        cursor = self._col.find(query).sort("learned_at", -1)
        docs = list(cursor)
        if len(docs) <= _MAX_PER_ACCOUNT:
            return
        for doc in docs[_MAX_PER_ACCOUNT:]:
            self._col.delete_one({"_id": doc["_id"]})
