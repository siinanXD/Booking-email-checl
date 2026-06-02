"""Gemeinsame Test-Fixtures."""

from __future__ import annotations

import json
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import mongomock
import pytest

from backend.ai.services.ingestion import IngestionService
from backend.ai.services.triage import TriageService
from backend.core.models.email import IncomingEmail
from backend.infrastructure.repositories.email_repository import EmailRepository
from backend.infrastructure.repositories.embedding_repository import EmbeddingRepository
from backend.infrastructure.repositories.entity_repository import EntityRepository
from backend.infrastructure.repositories.extraction_repository import (
    ExtractionRepository,
)
from backend.infrastructure.repositories.mongo import Db


@pytest.fixture
def mock_db() -> Generator[Db, None, None]:
    """In-Memory MongoDB via mongomock."""
    client: mongomock.MongoClient = mongomock.MongoClient()
    yield client["test_ai_email"]


@pytest.fixture
def email_repo(mock_db: Db) -> EmailRepository:
    """Execute the operation."""
    return EmailRepository(mock_db)


@pytest.fixture
def entity_repo(mock_db: Db) -> EntityRepository:
    """Execute the operation."""
    return EntityRepository(mock_db)


@pytest.fixture
def extraction_repo(mock_db: Db) -> ExtractionRepository:
    """Execute the operation."""
    return ExtractionRepository(mock_db)


@pytest.fixture
def embedding_repo(mock_db: Db) -> EmbeddingRepository:
    """Execute the operation."""
    return EmbeddingRepository(mock_db)


@pytest.fixture
def ingestion_service(email_repo: EmailRepository) -> IngestionService:
    """Execute the operation."""
    return IngestionService(email_repo, TriageService())


@pytest.fixture
def booking_emails() -> list[IncomingEmail]:
    """Lädt Fixture-Mails aus JSON."""
    path = Path(__file__).parent / "fixtures" / "booking_emails.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    result: list[IncomingEmail] = []
    for item in raw:
        item["received_at"] = datetime.fromisoformat(
            item["received_at"].replace("Z", "+00:00")
        )
        result.append(IncomingEmail.model_validate(item))
    return result
