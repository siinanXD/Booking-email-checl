"""Tests für Edit-Distanz-Tracking nach Review."""

from __future__ import annotations

from unittest.mock import MagicMock

from backend.infrastructure.observability.alerts import AlertService, AlertThresholds
from backend.infrastructure.observability.langfuse_client import LangfuseTracer
from backend.infrastructure.observability.review_feedback import ReviewFeedbackTracker


class _MockTracer(LangfuseTracer):
    def __init__(self) -> None:
        super().__init__(enabled=True)
        self._client = MagicMock()
        self.scores: list[tuple[str, str, float]] = []

    def log_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        self.scores.append((trace_id, name, value))


def test_identical_text_zero_distance() -> None:
    """Identischer Text ergibt Edit-Distanz 0.0."""
    tracer = _MockTracer()
    text = "Sehr geehrte/r Gast, Ihre Anfrage wurde bearbeitet."
    distance = ReviewFeedbackTracker().record("corr-1", text, text, tracer)
    assert distance == 0.0
    assert tracer.scores[0][1] == "draft_edit_distance"


def test_completely_different_text_near_one() -> None:
    """Komplett anderer Text ergibt Distanz nahe 1.0."""
    tracer = _MockTracer()
    distance = ReviewFeedbackTracker().record(
        "corr-2",
        "Sehr geehrte/r Gast, Ihre Anfrage wurde bearbeitet.",
        "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do",
        tracer,
    )
    assert distance >= 0.8


def test_typical_small_correction_moderate_distance() -> None:
    """Typische kleine Korrekturen liegen zwischen 0.1 und 0.4."""
    tracer = _MockTracer()
    draft = "Sehr geehrte/r Gast, Ihre Anfrage wurde bearbeitet."
    approved = "Sehr geehrter Gast, Ihre Anfrage wurde bearbeitet. Viele Grüße"
    distance = ReviewFeedbackTracker().record("corr-3", draft, approved, tracer)
    assert 0.1 <= distance <= 0.4


def test_high_edit_distance_triggers_alert(caplog) -> None:
    """Verify alert when edit distance exceeds configured threshold."""
    tracer = _MockTracer()
    alerts = AlertService(thresholds=AlertThresholds(max_draft_edit_distance=0.4))
    distance = ReviewFeedbackTracker(alerts=alerts).record(
        "corr-4",
        "Sehr geehrte/r Gast, Ihre Anfrage wurde bearbeitet.",
        "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do",
        tracer,
    )
    assert distance > 0.4
    assert any("draft_quality_low" in r.message for r in caplog.records)
