"""Retrieval-Tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.services.retrieval import RetrievalService
from backend.core.models.email import StoredEmail
from backend.core.models.entities import Guest, Reservation
from backend.infrastructure.observability.alerts import AlertService


def test_find_reservations_by_guest_email(
    entity_repo,
    email_repo,
) -> None:
    """Verify find reservations by guest email."""
    guest = Guest(guest_id="g1", email="guest@test.com", name="Max")
    entity_repo.upsert_guest(guest)
    entity_repo.upsert_reservation(
        Reservation(
            reservation_id="r1",
            guest_id="g1",
            booking_number="AB100",
            check_in=date(2026, 6, 1),
            check_out=date(2026, 6, 5),
        )
    )
    email = StoredEmail(
        message_id="m-ret-1",
        from_address="x@y.com",
        body_text="Hi",
        received_at=datetime.now(UTC),
    )
    email_repo.upsert_by_message_id(email)
    svc = RetrievalService(entity_repo, email_repo)
    hits = svc.retrieve(
        email,
        BookingExtraction(email="guest@test.com", booking_number="AB100"),
    )
    assert len(hits.reservations) >= 1
    assert hits.reservations[0].booking_number == "AB100"


def test_retrieve_returns_empty_list_not_none(
    entity_repo,
    email_repo,
) -> None:
    """Leeres Retrieval liefert [] statt None."""
    email = StoredEmail(
        message_id="m-ret-empty",
        from_address="x@y.com",
        body_text="Hi",
        received_at=datetime.now(UTC),
    )
    email_repo.upsert_by_message_id(email)
    hits = RetrievalService(entity_repo, email_repo).retrieve(email)
    assert hits.reservations == []


def test_retrieve_truncates_reservations(
    entity_repo,
    email_repo,
    caplog,
) -> None:
    """Mehr als max_reservations wird gekürzt und geloggt."""
    guest = Guest(guest_id="g-many", email="many@test.com")
    entity_repo.upsert_guest(guest)
    for i in range(25):
        entity_repo.upsert_reservation(
            Reservation(
                reservation_id=f"r{i}",
                guest_id="g-many",
                booking_number=f"BN{i}",
            )
        )
    email = StoredEmail(
        message_id="m-ret-trunc",
        from_address="many@test.com",
        body_text="Hi",
        received_at=datetime.now(UTC),
    )
    email_repo.upsert_by_message_id(email)
    hits = RetrievalService(entity_repo, email_repo).retrieve(
        email,
        BookingExtraction(email="many@test.com"),
        max_reservations=20,
    )
    assert len(hits.reservations) == 20
    assert any("retrieval_truncated" in r.message for r in caplog.records)


def test_retrieve_alerts_on_missing_booking_number(
    entity_repo,
    email_repo,
    caplog,
) -> None:
    """Bekannte Buchungsnummer ohne Treffer löst Alert aus."""
    email = StoredEmail(
        message_id="m-ret-alert",
        from_address="x@y.com",
        body_text="Hi",
        received_at=datetime.now(UTC),
        correlation_id="corr-ret-alert",
    )
    email_repo.upsert_by_message_id(email)
    alerts = AlertService()
    svc = RetrievalService(entity_repo, email_repo, alerts=alerts)
    svc.retrieve(
        email,
        BookingExtraction(booking_number="MISSING99"),
    )
    assert any("retrieval_empty" in r.message for r in caplog.records)
