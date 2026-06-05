"""Indexierung und Chunking."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from pymongo.errors import OperationFailure

from backend.ai.services.indexing import IndexingService
from backend.infrastructure.observability.alerts import AlertService
from backend.infrastructure.repositories.embedding_repository import (
    VECTOR_INDEX_NAME,
    EmbeddingRepository,
)


def test_search_by_vector_atlas_uses_aggregate(mock_db) -> None:
    """Verify atlas search delegates to aggregate pipeline."""
    repo = EmbeddingRepository(mock_db)
    with patch.object(
        repo._col,
        "aggregate",
        return_value=[{"_id": "c1", "text": "hello"}],
    ) as aggregate_mock:
        results = repo.search_by_vector_atlas([1.0, 0.0], limit=2)
        assert len(results) == 1
        aggregate_mock.assert_called_once()
        pipeline = aggregate_mock.call_args[0][0]
        assert pipeline[0]["$vectorSearch"]["index"] == VECTOR_INDEX_NAME


def test_search_by_vector_atlas_returns_empty_when_offline(
    mock_db,
    caplog,
) -> None:
    """Atlas offline → leere Liste, KEIN In-Memory-Fallback, Warnung im Log."""
    import logging

    repo = EmbeddingRepository(mock_db)
    repo.upsert_chunk("c1", "corr-1", "hello", [1.0, 0.0], "guest_inquiry")
    with (
        patch.object(
            repo._col,
            "aggregate",
            side_effect=OperationFailure("vector search unavailable"),
        ),
        caplog.at_level(logging.WARNING),
    ):
        results = repo.search_by_vector_atlas(
            [1.0, 0.0],
            limit=1,
            filter={"correlation_id": "corr-1"},
        )
    assert results == []
    assert any("vektordatenbank_offline" in r.message for r in caplog.records)


def test_index_async_alerts_on_failure(mock_db) -> None:
    """Verify async indexing emits alert with indexing: prefix on failure."""

    class FailingEmbed:
        def embed(self, text: str) -> list[float]:
            raise RuntimeError("embed failed")

    alerts = MagicMock(spec=AlertService)
    repo = EmbeddingRepository(mock_db)
    svc = IndexingService(repo, FailingEmbed(), alerts=alerts)
    asyncio.run(svc._index_async("corr-fail", "hello world", None))
    alerts.check_extraction_failure.assert_called_once()
    args = alerts.check_extraction_failure.call_args[0]
    assert args[0] == "corr-fail"
    assert args[1].startswith("indexing:")
