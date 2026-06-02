"""Provider-unabhängiger Mail-Poll → Workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from adapters.mail_connector import build_mail_connector
from config.settings import Settings
from repositories.email_repository import EmailRepository
from repositories.mail_connection_repository import MailConnectionRepository
from workflows.email_workflow import EmailWorkflow

logger = logging.getLogger(__name__)


@dataclass
class MailPollItemResult:
    """Ergebnis einer einzelnen Mail."""

    message_id: str
    ingested: bool
    duplicate: bool
    error: str | None = None


@dataclass
class MailPollRunResult:
    """Gesamtergebnis eines Poll-Laufs."""

    processed: int
    items: list[MailPollItemResult]


class MailIngestionRunner:
    """Holt Mails über MailConnector und startet den Email-Workflow."""

    def __init__(
        self,
        mail_connection_repo: MailConnectionRepository,
        workflow: EmailWorkflow,
        email_repo: EmailRepository,
        settings: Settings,
        *,
        fetch_max: int = 100,
        fetch_unread_only: bool = False,
    ) -> None:
        """Initialize the instance with its dependencies."""
        self._mail_repo_conn = mail_connection_repo
        self._workflow = workflow
        self._email_repo = email_repo
        self._settings = settings
        self._fetch_max = fetch_max
        self._fetch_unread_only = fetch_unread_only

    def run_for_account(self, account_id: str) -> MailPollRunResult:
        """Pollt Postfach eines Accounts."""
        record = self._mail_repo_conn.get(account_id)
        if record is None:
            logger.warning("No mail connection for account %s", account_id)
            return MailPollRunResult(processed=0, items=[])
        connector = build_mail_connector(record, self._settings)
        messages = connector.fetch_messages(
            limit=self._fetch_max,
            unread_only=self._fetch_unread_only,
        )
        items: list[MailPollItemResult] = []
        for payload in messages:
            existing = self._email_repo.get_by_message_id(
                payload.message_id,
                account_id=account_id,
            )
            if existing is not None:
                items.append(
                    MailPollItemResult(
                        message_id=payload.message_id,
                        ingested=False,
                        duplicate=True,
                    )
                )
                continue
            try:
                result = self._workflow.run(payload, thread_id=payload.correlation_id)
                duplicate = bool(result.get("ingest_duplicate"))
                items.append(
                    MailPollItemResult(
                        message_id=payload.message_id,
                        ingested=not duplicate,
                        duplicate=duplicate,
                    )
                )
            except Exception as exc:
                logger.exception("Workflow failed for %s", payload.message_id)
                items.append(
                    MailPollItemResult(
                        message_id=payload.message_id,
                        ingested=False,
                        duplicate=False,
                        error=str(exc),
                    )
                )
        processed = sum(1 for item in items if item.ingested)
        return MailPollRunResult(processed=processed, items=items)

    def run_all_pollable(
        self,
        account_ids: list[str] | None = None,
    ) -> dict[str, MailPollRunResult]:
        """Pollt mehrere Accounts (optional gefiltert)."""
        records = self._mail_repo_conn.list_pollable()
        if account_ids is not None:
            allowed = set(account_ids)
            records = [r for r in records if r.account_id in allowed]
        results: dict[str, MailPollRunResult] = {}
        for record in records:
            results[record.account_id] = self.run_for_account(record.account_id)
        return results
