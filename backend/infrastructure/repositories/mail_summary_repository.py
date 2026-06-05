"""Persistenz von Mail-Zusammenfassungen."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.collection import Collection

from backend.core.models.mail_summary import MailSummary
from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter


class MailSummaryRepository:
    """Collection `mail_summaries`."""

    COLLECTION = "mail_summaries"

    def __init__(self, db: Db) -> None:
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def upsert(self, summary: MailSummary, *, account_id: str) -> MailSummary:
        now = datetime.now(UTC)
        doc: dict[str, Any] = {
            "_id": summary.correlation_id,
            "correlation_id": summary.correlation_id,
            "summary_text": summary.summary_text,
            "sentiment": summary.sentiment,
            "source": summary.source,
            "updated_at": now.isoformat(),
            "account_id": account_id,
        }
        self._col.update_one(
            {"_id": summary.correlation_id},
            {"$set": doc},
            upsert=True,
        )
        return MailSummary.model_validate({**doc, "updated_at": now})

    def get(
        self,
        correlation_id: str,
        *,
        account_id: str,
    ) -> MailSummary | None:
        query = with_account_filter({"_id": correlation_id}, account_id)
        doc = self._col.find_one(query)
        if doc is None:
            return None
        return MailSummary.model_validate(doc)
