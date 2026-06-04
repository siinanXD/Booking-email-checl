"""Unit-Tests für Admin-Aktivitäts-Heuristik."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.api.services.admin_overview_queries import activity_status


def test_activity_status_active_on_recent_sync() -> None:
    now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
    status = activity_status(
        last_sync_at=now - timedelta(days=2),
        last_email_received_at=None,
        last_review_at=None,
        has_metric_7d=False,
        now=now,
    )
    assert status == "active"


def test_activity_status_idle_with_old_activity() -> None:
    now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
    status = activity_status(
        last_sync_at=now - timedelta(days=30),
        last_email_received_at=None,
        last_review_at=None,
        has_metric_7d=False,
        now=now,
    )
    assert status == "idle"


def test_activity_status_never_without_signals() -> None:
    status = activity_status(
        last_sync_at=None,
        last_email_received_at=None,
        last_review_at=None,
        has_metric_7d=False,
    )
    assert status == "never"


def test_activity_status_active_on_metric_flag() -> None:
    status = activity_status(
        last_sync_at=None,
        last_email_received_at=None,
        last_review_at=None,
        has_metric_7d=True,
    )
    assert status == "active"
