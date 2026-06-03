"""Plattform-Admin: Verbindungstests pro Mandant."""

from __future__ import annotations

import time
from collections import defaultdict

from backend.api.schemas.admin_diagnostics import (
    AdminWhatsAppInfoResponse,
    AdminWhatsAppTestRequest,
    AdminWhatsAppTestResponse,
    WhatsAppTestTemplate,
)
from backend.api.schemas.mail import MailConnectionResponse, MailTestResponse
from backend.core.config.factory import AppContext
from backend.core.config.settings import Settings
from backend.features.mail.mail_connection_service import MailConnectionService
from backend.features.notifications.whatsapp_client import send_whatsapp_admin_test
from backend.features.platform.effective_settings import (
    display_platform_settings,
    merge_platform_settings,
    platform_from_env,
)
from backend.infrastructure.repositories.account_repository import AccountRecord

_TEST_WINDOW_SEC = 60
_TEST_MAX_PER_WINDOW = 5
_recent_tests: dict[str, list[float]] = defaultdict(list)


class AccountNotFoundError(Exception):
    """Unbekannte account_id."""


class RateLimitExceededError(Exception):
    """Zu viele Diagnose-Tests für einen Mandanten."""


class AdminDiagnosticsService:
    """Mail- und WhatsApp-Diagnose im Auftrag eines Mandanten."""

    def __init__(self, ctx: AppContext, settings: Settings) -> None:
        self._ctx = ctx
        self._settings = settings

    def get_mail_connection(self, account_id: str) -> MailConnectionResponse:
        """Liest Postfach-Status (read-only, ohne Passwörter)."""
        self._require_account(account_id)
        return self._mail_service().get_response(account_id)

    def test_mail_connection(self, account_id: str) -> MailTestResponse:
        """Testet die gespeicherte Postfach-Verbindung des Mandanten."""
        self._require_account(account_id)
        self._check_rate_limit(account_id, "mail")
        result = self._mail_service().test_connection(account_id)
        return MailTestResponse(
            success=result.success,
            message=result.message,
            mailbox_count=result.mailbox_count,
        )

    def get_whatsapp_info(self, account_id: str) -> AdminWhatsAppInfoResponse:
        """WhatsApp-Konfiguration ohne Tokens."""
        self._require_account(account_id)
        platform = self._ctx.platform_settings_repo.get(account_id)
        display = display_platform_settings(
            self._settings,
            platform if platform else platform_from_env(self._settings, account_id),
        )
        return AdminWhatsAppInfoResponse(
            whatsapp_enabled=display.whatsapp_enabled,
            access_token_configured=bool(display.whatsapp_access_token.strip()),
            phone_number_id=display.whatsapp_phone_number_id,
            test_recipient=display.whatsapp_test_recipient,
            template_language=display.whatsapp_template_language,
            templates={
                "cleaning_task": display.whatsapp_template_cleaning_task,
                "status_notice": display.whatsapp_template_status_notice,
                "guest_inquiry": display.whatsapp_template_guest_inquiry,
            },
        )

    def test_whatsapp(
        self,
        account_id: str,
        body: AdminWhatsAppTestRequest,
    ) -> AdminWhatsAppTestResponse:
        """Sendet Test-Template mit Mandanten-Credentials."""
        self._require_account(account_id)
        self._check_rate_limit(account_id, "whatsapp")
        platform = self._ctx.platform_settings_repo.get(account_id)
        effective = merge_platform_settings(self._settings, platform)
        info = self.get_whatsapp_info(account_id)
        recipient = (body.recipient_e164 or info.test_recipient or "").strip()
        if not recipient:
            return AdminWhatsAppTestResponse(
                success=False,
                template=body.template,
                error="Keine Test-Nummer konfiguriert (whatsapp_test_recipient).",
            )
        result = send_whatsapp_admin_test(
            effective,
            recipient,
            body.template,
        )
        template_name = _resolved_template_name(effective, body.template)
        return AdminWhatsAppTestResponse(
            success=result.success,
            template=body.template,
            template_name=template_name,
            provider_message_id=result.provider_message_id,
            error=result.error,
        )

    def _require_account(self, account_id: str) -> AccountRecord:
        account = self._ctx.account_repo.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(account_id)
        return account

    def _mail_service(self) -> MailConnectionService:
        return MailConnectionService(
            self._ctx.mail_connection_repo,
            self._ctx.platform_settings_repo,
            self._settings,
        )

    @staticmethod
    def _check_rate_limit(account_id: str, kind: str) -> None:
        key = f"{account_id}:{kind}"
        now = time.monotonic()
        window = _recent_tests[key]
        _recent_tests[key] = [t for t in window if now - t < _TEST_WINDOW_SEC]
        if len(_recent_tests[key]) >= _TEST_MAX_PER_WINDOW:
            raise RateLimitExceededError
        _recent_tests[key].append(now)


def _resolved_template_name(
    settings: Settings,
    template: WhatsAppTestTemplate,
) -> str | None:
    if template == "hello_world":
        return "hello_world"
    if template == "cleaning_task":
        return settings.whatsapp_template_cleaning_task
    if template == "status_notice":
        return settings.whatsapp_template_status_notice
    if template == "guest_inquiry":
        return settings.whatsapp_template_guest_inquiry
    return None
