"""Löscht Anwendungsdaten pro Mandant – Benutzer bleiben."""

from __future__ import annotations

from typing import Any

from pymongo.database import Database

from repositories.email_repository import EmailRepository
from repositories.embedding_repository import EmbeddingRepository
from repositories.extraction_repository import ExtractionRepository
from repositories.mail_metrics_repository import MailMetricsRepository
from repositories.notification_repository import NotificationRepository
from repositories.platform_settings_repository import PlatformSettingsRepository
from repositories.property_recipient_repository import PropertyRecipientRepository
from repositories.review_repository import ReviewRepository

WIPE_COLLECTIONS = (
    EmailRepository.COLLECTION,
    ExtractionRepository.COLLECTION,
    EmbeddingRepository.COLLECTION,
    ReviewRepository.COLLECTION,
    MailMetricsRepository.COLLECTION,
    NotificationRepository.COLLECTION,
    PropertyRecipientRepository.COLLECTION,
    PlatformSettingsRepository.COLLECTION,
    "mail_connections",
    "guests",
    "reservations",
)


class DataWipeService:
    """Entfernt Betriebsdaten eines Mandanten aus MongoDB."""

    def __init__(self, db: Database[Any]) -> None:
        """Initialize the instance with its dependencies."""
        self._db = db

    def wipe_account(self, account_id: str) -> dict[str, int]:
        """Löscht alle Betriebsdaten eines Accounts."""
        counts: dict[str, int] = {}
        for name in WIPE_COLLECTIONS:
            if name == PlatformSettingsRepository.COLLECTION:
                result = self._db[name].delete_many({"_id": account_id})
            else:
                result = self._db[name].delete_many({"account_id": account_id})
            counts[name] = int(result.deleted_count)
        return counts

    def wipe_all(self) -> dict[str, int]:
        """Legacy: löscht alle Betriebsdaten global (nur Migration/Tests)."""
        counts: dict[str, int] = {}
        for name in WIPE_COLLECTIONS:
            result = self._db[name].delete_many({})
            counts[name] = int(result.deleted_count)
        return counts
