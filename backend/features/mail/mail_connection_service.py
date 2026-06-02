"""Fachlogik für Postfach-Verbindungen."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.api.schemas.mail import ImapPresetItem, MailConnectionResponse
from backend.core.config.settings import Settings
from backend.features.mail.presets import IMAP_PRESETS
from backend.infrastructure.adapters.mail.connector import (
    MailTestResult,
    build_mail_connector,
)
from backend.infrastructure.repositories.mail_connection_repository import (
    MailConnectionRecord,
    MailConnectionRepository,
    MailConnectionStatus,
)
from backend.infrastructure.repositories.platform_settings_repository import (
    PlatformSettingsRepository,
)


class MailConnectionService:
    """Verwaltet Mail-Verbindungen pro Account."""

    def __init__(
        self,
        mail_repo: MailConnectionRepository,
        platform_settings_repo: PlatformSettingsRepository,
        settings: Settings,
    ) -> None:
        """Initialize the instance with its dependencies."""
        self._mail_repo = mail_repo
        self._platform_settings_repo = platform_settings_repo
        self._settings = settings

    def get_response(self, account_id: str) -> MailConnectionResponse:
        """Lädt Verbindung als API-DTO."""
        record = self._mail_repo.get_or_create(account_id)
        return self._to_response(record)

    def apply_update(
        self,
        account_id: str,
        update: object,
    ) -> MailConnectionResponse:
        """Wendet partielle Aktualisierung an."""
        from backend.api.schemas.mail import MailConnectionUpdate

        assert isinstance(update, MailConnectionUpdate)
        record = self._mail_repo.get_or_create(account_id)

        if update.provider is not None:
            record.provider = update.provider  # type: ignore[assignment]
        if update.email_address is not None:
            record.email_address = update.email_address.strip()
        if update.preset is not None:
            record.preset = update.preset.strip() or None
            if record.preset and record.preset in IMAP_PRESETS:
                preset = IMAP_PRESETS[record.preset]
                if preset["host"]:
                    record.imap_host = preset["host"]
                record.imap_port = preset["port"]
                record.imap_use_ssl = preset["use_ssl"]
        if update.imap_host is not None:
            record.imap_host = update.imap_host.strip()
        if update.imap_port is not None:
            record.imap_port = update.imap_port
        if update.imap_username is not None:
            record.imap_username = update.imap_username.strip()
        if update.imap_password is not None and update.imap_password.strip():
            record.imap_password = update.imap_password.strip()
        if update.imap_use_ssl is not None:
            record.imap_use_ssl = update.imap_use_ssl
        if update.outlook_auth_mode is not None:
            record.outlook_auth_mode = update.outlook_auth_mode.strip()
        if update.outlook_mailbox is not None:
            record.outlook_mailbox = update.outlook_mailbox.strip()
        if update.onboarding_completed is not None:
            record.onboarding_completed = update.onboarding_completed

        if record.provider == "outlook":
            mailbox = record.outlook_mailbox or record.email_address
            platform = self._platform_settings_repo.get(account_id)
            if platform is None:
                from backend.features.platform.effective_settings import (
                    platform_from_env,
                )

                platform = platform_from_env(self._settings, account_id)
            platform.outlook_mailbox = mailbox
            self._platform_settings_repo.save(platform)

        self._mail_repo.save(record)
        return self._to_response(record)

    def test_connection(self, account_id: str) -> MailTestResult:
        """Testet die gespeicherte Verbindung."""
        record = self._mail_repo.get(account_id)
        if record is None:
            return MailTestResult(
                success=False, message="Keine Konfiguration vorhanden."
            )
        connector = build_mail_connector(record, self._settings)
        result = connector.test_connection()
        conn_status: MailConnectionStatus = "connected" if result.success else "error"
        self._mail_repo.update_status(
            account_id,
            conn_status,
            last_error=None if result.success else result.message,
            last_sync_at=datetime.now(UTC) if result.success else None,
        )
        return result

    def _to_response(self, record: MailConnectionRecord) -> MailConnectionResponse:
        presets = [
            ImapPresetItem(
                id=key,
                label=value["label"],
                host=value["host"],
                port=value["port"],
                use_ssl=value["use_ssl"],
            )
            for key, value in IMAP_PRESETS.items()
        ]
        last_sync = (
            record.last_sync_at.isoformat() if record.last_sync_at is not None else None
        )
        return MailConnectionResponse(
            provider=record.provider,
            status=record.status,
            email_address=record.email_address,
            preset=record.preset,
            imap_host=record.imap_host,
            imap_port=record.imap_port,
            imap_username=record.imap_username,
            imap_password_set=bool(record.imap_password.strip()),
            imap_use_ssl=record.imap_use_ssl,
            outlook_auth_mode=record.outlook_auth_mode,
            outlook_mailbox=record.outlook_mailbox or record.email_address,
            outlook_oauth_connected=bool(record.outlook_token_cache.strip()),
            last_error=record.last_error,
            last_sync_at=last_sync,
            onboarding_completed=record.onboarding_completed,
            imap_presets=presets,
        )
