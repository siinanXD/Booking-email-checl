"""Tests für automatisches Mail-Polling."""

from __future__ import annotations

from unittest.mock import MagicMock

from backend.features.mail.mail_poll_service import MailPollService
from backend.infrastructure.adapters.mail.ingestion import (
    MailPollItemResult,
    MailPollRunResult,
)
from backend.infrastructure.repositories.account_repository import AccountRepository
from backend.infrastructure.repositories.mail_connection_repository import (
    MailConnectionRecord,
    MailConnectionRepository,
)
from backend.infrastructure.repositories.mongo import Db


def _active_account(
    account_repo: AccountRepository, *, email: str = "a@test.local"
) -> str:
    account = account_repo.create(
        display_name="Active",
        contact_email=email,
        status="active",
    )
    return account.id


def _pending_account(account_repo: AccountRepository) -> str:
    account = account_repo.create(
        display_name="Pending",
        contact_email="pending@test.local",
        status="pending",
    )
    return account.id


def _save_mail(
    mail_repo: MailConnectionRepository,
    account_id: str,
    *,
    provider: str = "imap",
    onboarding_completed: bool = True,
    imap_password: str = "secret",
    imap_host: str = "imap.gmx.net",
    email_address: str = "user@gmx.de",
) -> None:
    record = MailConnectionRecord(
        account_id=account_id,
        provider=provider,  # type: ignore[arg-type]
        onboarding_completed=onboarding_completed,
        imap_host=imap_host,
        imap_username=email_address,
        imap_password=imap_password,
        email_address=email_address,
    )
    mail_repo.save(record)


def test_is_pollable_imap_requires_credentials() -> None:
    complete = MailConnectionRecord(
        account_id="a1",
        provider="imap",
        onboarding_completed=True,
        imap_host="imap.gmx.net",
        imap_username="u@gmx.de",
        imap_password="pw",
        email_address="u@gmx.de",
    )
    incomplete = MailConnectionRecord(
        account_id="a2",
        provider="imap",
        onboarding_completed=True,
        imap_host="imap.gmx.net",
        email_address="u@gmx.de",
    )
    assert MailConnectionRepository.is_pollable(complete) is True
    assert MailConnectionRepository.is_pollable(incomplete) is False


def test_is_pollable_outlook_requires_mailbox() -> None:
    complete = MailConnectionRecord(
        account_id="a1",
        provider="outlook",
        onboarding_completed=True,
        outlook_mailbox="box@example.com",
    )
    skipped_onboarding = MailConnectionRecord(
        account_id="a2",
        provider="outlook",
        onboarding_completed=False,
        outlook_mailbox="box@example.com",
    )
    assert MailConnectionRepository.is_pollable(complete) is True
    assert MailConnectionRepository.is_pollable(skipped_onboarding) is False


def test_list_pollable_filters_incomplete(mock_db: Db) -> None:
    mail_repo = MailConnectionRepository(mock_db)
    _save_mail(mail_repo, "acc1")
    _save_mail(
        mail_repo,
        "acc2",
        onboarding_completed=True,
        imap_password="",
    )
    pollable = mail_repo.list_pollable()
    assert len(pollable) == 1
    assert pollable[0].account_id == "acc1"


def test_run_all_skips_non_active_accounts(mock_db: Db) -> None:
    account_repo = AccountRepository(mock_db)
    mail_repo = MailConnectionRepository(mock_db)
    active_id = _active_account(account_repo)
    pending_id = _pending_account(account_repo)
    _save_mail(mail_repo, active_id)
    _save_mail(mail_repo, pending_id, email_address="p@gmx.de")

    runner = MagicMock()
    runner.run_for_account.return_value = MailPollRunResult(processed=1, items=[])
    service = MailPollService(mail_repo, account_repo, runner)

    result = service.run_all()

    assert result.accounts_polled == 1
    runner.run_for_account.assert_called_once_with(active_id)


def test_run_all_continues_after_account_error(mock_db: Db) -> None:
    account_repo = AccountRepository(mock_db)
    mail_repo = MailConnectionRepository(mock_db)
    acc1 = _active_account(account_repo, email="one@test.local")
    acc2 = _active_account(account_repo, email="two@test.local")
    _save_mail(mail_repo, acc1, email_address="one@gmx.de")
    _save_mail(mail_repo, acc2, email_address="two@gmx.de")

    runner = MagicMock()

    def _run(account_id: str) -> MailPollRunResult:
        if account_id == acc1:
            raise ConnectionError("IMAP down")
        return MailPollRunResult(processed=2, items=[])

    runner.run_for_account.side_effect = _run
    service = MailPollService(mail_repo, account_repo, runner)

    result = service.run_all()

    assert result.accounts_polled == 2
    assert result.total_processed == 2
    assert runner.run_for_account.call_count == 2


def test_run_all_updates_connection_status(mock_db: Db) -> None:
    account_repo = AccountRepository(mock_db)
    mail_repo = MailConnectionRepository(mock_db)
    account_id = _active_account(account_repo)
    _save_mail(mail_repo, account_id)

    runner = MagicMock()
    runner.run_for_account.return_value = MailPollRunResult(
        processed=1,
        items=[
            MailPollItemResult(
                message_id="m1",
                ingested=True,
                duplicate=False,
            )
        ],
    )
    service = MailPollService(mail_repo, account_repo, runner)
    service.run_all()

    record = mail_repo.get(account_id)
    assert record is not None
    assert record.status == "connected"
    assert record.last_error is None
    assert record.last_sync_at is not None


def test_run_all_sets_error_status_on_fetch_failure(mock_db: Db) -> None:
    account_repo = AccountRepository(mock_db)
    mail_repo = MailConnectionRepository(mock_db)
    account_id = _active_account(account_repo)
    _save_mail(mail_repo, account_id)

    runner = MagicMock()
    runner.run_for_account.side_effect = RuntimeError("auth failed")
    service = MailPollService(mail_repo, account_repo, runner)
    service.run_all()

    record = mail_repo.get(account_id)
    assert record is not None
    assert record.status == "error"
    assert record.last_error == "auth failed"


def test_run_all_records_item_errors_with_connected_status(mock_db: Db) -> None:
    account_repo = AccountRepository(mock_db)
    mail_repo = MailConnectionRepository(mock_db)
    account_id = _active_account(account_repo)
    _save_mail(mail_repo, account_id)

    runner = MagicMock()
    runner.run_for_account.return_value = MailPollRunResult(
        processed=0,
        items=[
            MailPollItemResult(
                message_id="m1",
                ingested=False,
                duplicate=False,
                error="workflow boom",
            )
        ],
    )
    service = MailPollService(mail_repo, account_repo, runner)
    service.run_all()

    record = mail_repo.get(account_id)
    assert record is not None
    assert record.status == "connected"
    assert record.last_error == "workflow boom"
    assert record.last_sync_at is not None
