"""Persistierte API-Kosten pro verarbeiteter Mail."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter


class MailMetricRecord(BaseModel):
    """Kosten-Snapshot einer Mail."""

    correlation_id: str
    cost_usd: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MailMetricsRepository:
    """Collection `mail_metrics`."""

    COLLECTION = "mail_metrics"

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def record(
        self,
        correlation_id: str,
        *,
        cost_usd: float,
        prompt_tokens: int,
        completion_tokens: int,
        account_id: str | None = None,
    ) -> None:
        """Speichert Kosten-Snapshot (idempotent pro correlation_id)."""
        doc: dict[str, Any] = {
            "_id": correlation_id,
            "correlation_id": correlation_id,
            "cost_usd": cost_usd,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "processed_at": datetime.now(UTC).isoformat(),
        }
        if account_id:
            doc["account_id"] = account_id
        self._col.update_one({"_id": correlation_id}, {"$set": doc}, upsert=True)

    def sum_cost_between(
        self,
        start: datetime,
        end: datetime,
        *,
        account_id: str | None = None,
    ) -> float:
        """Summiert Kosten im Zeitraum."""
        match = with_account_filter(
            {
                "processed_at": {
                    "$gte": start.isoformat(),
                    "$lte": end.isoformat(),
                }
            },
            account_id,
        )
        pipeline: Sequence[Mapping[str, Any]] = [
            {"$match": match},
            {"$group": {"_id": None, "total": {"$sum": "$cost_usd"}}},
        ]
        rows = list(self._col.aggregate(pipeline))
        if not rows:
            return 0.0
        return float(rows[0].get("total", 0.0))

    def count_between(
        self,
        start: datetime,
        end: datetime,
        *,
        account_id: str | None = None,
    ) -> int:
        """Anzahl Metrik-Einträge im Zeitraum."""
        query = with_account_filter(
            {
                "processed_at": {
                    "$gte": start.isoformat(),
                    "$lte": end.isoformat(),
                }
            },
            account_id,
        )
        return int(self._col.count_documents(query))

    def aggregate_by_day(
        self,
        start: datetime,
        end: datetime,
        *,
        account_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Tagesaggregation für Kosten-Charts."""
        match = with_account_filter(
            {
                "processed_at": {
                    "$gte": start.isoformat(),
                    "$lte": end.isoformat(),
                }
            },
            account_id,
        )
        pipeline: Sequence[Mapping[str, Any]] = [
            {"$match": match},
            {
                "$group": {
                    "_id": {"$substr": ["$processed_at", 0, 10]},
                    "cost_usd": {"$sum": "$cost_usd"},
                    "total_tokens": {
                        "$sum": {"$add": ["$prompt_tokens", "$completion_tokens"]}
                    },
                    "mail_count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        series: list[dict[str, Any]] = []
        for row in self._col.aggregate(pipeline):
            series.append(
                {
                    "date": row["_id"],
                    "cost_usd": round(float(row.get("cost_usd", 0.0)), 4),
                    "total_tokens": int(row.get("total_tokens", 0)),
                    "mail_count": int(row.get("mail_count", 0)),
                }
            )
        return series

    def top_expensive(self, limit: int = 10) -> list[MailMetricRecord]:
        """Teuerste Mails."""
        cursor = self._col.find().sort("cost_usd", -1).limit(limit)
        return [MailMetricRecord.model_validate(doc) for doc in cursor]
