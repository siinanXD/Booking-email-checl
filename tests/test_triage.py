"""Tests für regelbasierte Triage und LLM-Gate."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.triage import TriageOutcome
from backend.ai.services.triage import TriageService
from backend.core.models.email import IncomingEmail
from tests.mocks import MockLLM


def test_triage_relevant_booking() -> None:
    """Verify triage relevant booking."""
    email = IncomingEmail(
        message_id="m1",
        from_address="guest@airbnb.com",
        subject="Buchung",
        body_text="Neue Reservierung",
        received_at=datetime.now(UTC),
        platform="airbnb",
    )
    result = TriageService(triage_llm_enabled=False).triage(email)
    assert result.outcome == TriageOutcome.RELEVANT


def test_triage_gmail_with_booking_keywords() -> None:
    """Unbekannte Domain mit Buchungs-Keywords → RELEVANT ohne LLM."""
    email = IncomingEmail(
        message_id="m-gmail",
        from_address="guest@gmail.com",
        subject="Frage zur Reservierung",
        body_text="Wann kann ich einchecken?",
        received_at=datetime.now(UTC),
    )
    result = TriageService(triage_llm_enabled=False).triage(email)
    assert result.outcome == TriageOutcome.RELEVANT
    assert result.reason in ("booking_heuristic", "unknown_domain_with_signals")


def test_triage_phishing() -> None:
    """Verify triage phishing."""
    email = IncomingEmail(
        message_id="m2",
        from_address="x@evil.com",
        subject="Urgent",
        body_text="Click here immediately verify your account",
        received_at=datetime.now(UTC),
    )
    result = TriageService(triage_llm_enabled=False).triage(email)
    assert result.outcome == TriageOutcome.SPAM_PHISHING


def test_triage_empty_noreply() -> None:
    """Verify triage empty noreply."""
    email = IncomingEmail(
        message_id="m3",
        from_address="noreply@mailer-daemon.local",
        subject="",
        body_text="",
        received_at=datetime.now(UTC),
    )
    result = TriageService(triage_llm_enabled=False).triage(email)
    assert result.outcome == TriageOutcome.SPAM_PHISHING


def test_triage_marketing_linkedin() -> None:
    """LinkedIn-Benachrichtigung → SPAM vor LLM."""
    email = IncomingEmail(
        message_id="m-li",
        from_address="messages-noreply@linkedin.com",
        subject="Sie haben eine neue Verbindung",
        body_text="Profil ansehen",
        received_at=datetime.now(UTC),
    )
    result = TriageService(triage_llm_enabled=False).triage(email)
    assert result.outcome == TriageOutcome.SPAM_PHISHING
    assert result.reason == "marketing_noise"


def test_triage_unknown_domain_no_signals_discarded() -> None:
    """Unbekannte Domain ohne Signale → SPAM (Heuristik, kein LLM)."""
    email = IncomingEmail(
        message_id="m4",
        from_address="unknown@random.org",
        subject="Hello",
        body_text="Generic inquiry",
        received_at=datetime.now(UTC),
        platform="airbnb",
    )
    result = TriageService(triage_llm_enabled=False).triage(email)
    assert result.outcome == TriageOutcome.SPAM_PHISHING
    assert result.reason == "unknown_domain_no_signals"


def test_triage_unknown_domain_llm_relevant() -> None:
    """LLM-Gate kann unklare Mails als relevant einstufen."""
    email = IncomingEmail(
        message_id="m5",
        from_address="guest@weird-startup.io",
        subject="Meeting",
        body_text="Please confirm our apartment appointment",
        received_at=datetime.now(UTC),
    )
    result = TriageService(llm=MockLLM(), triage_llm_enabled=True).triage(email)
    assert result.outcome == TriageOutcome.RELEVANT
    assert result.reason == "unknown_domain_llm_relevant"


def test_triage_unknown_domain_llm_spam() -> None:
    """LLM-Gate verwirft generische Fremdmail."""
    email = IncomingEmail(
        message_id="m6",
        from_address="unknown@random.org",
        subject="Hello",
        body_text="Generic inquiry",
        received_at=datetime.now(UTC),
    )
    result = TriageService(llm=MockLLM(), triage_llm_enabled=True).triage(email)
    assert result.outcome == TriageOutcome.SPAM_PHISHING
    assert result.reason == "unknown_domain_llm_spam"
