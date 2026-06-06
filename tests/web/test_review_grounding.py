"""Review-API-Tests: Grounding-Filter und Ground-Zero-Endpoint."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.core.models.email import StoredEmail
from backend.infrastructure.repositories.review_repository import ReviewRepository


def test_pending_grounding_filter(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    mock_db: object,
    email_repo: Any,
) -> None:
    """GET /api/review/pending?grounding=1 filtert nach grounding_flag."""
    reviews = ReviewRepository(mock_db)  # type: ignore[arg-type]
    for cid, flagged in (("corr-g1", True), ("corr-g2", False)):
        email_repo.upsert_by_message_id(
            StoredEmail(
                message_id=f"m-{cid}",
                from_address="a@test.local",
                subject="Test",
                body_text="body",
                received_at=datetime.now(UTC),
                correlation_id=cid,
                account_id=tenant_account_id,
            )
        )
        reviews.upsert_pending(
            correlation_id=cid,
            message_id=f"m-{cid}",
            draft_body="draft",
            grounding_flag=flagged,
            intent="new_booking",
            account_id=tenant_account_id,
        )
    resp = client.get(
        "/api/review/pending?grounding=1",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    ids = {item["correlation_id"] for item in resp.get_json()["items"]}
    assert "corr-g1" in ids
    assert "corr-g2" not in ids


def test_list_ground_zero_endpoint(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    mock_db: object,
    email_repo: Any,
) -> None:
    """GET /api/review/ground-zero liefert offene Grounding-Fälle."""
    reviews = ReviewRepository(mock_db)  # type: ignore[arg-type]
    for cid, flagged, status in (
        ("corr-gz1", True, "pending"),
        ("corr-gz2", False, "pending"),
        ("corr-gz3", True, "approved"),
    ):
        email_repo.upsert_by_message_id(
            StoredEmail(
                message_id=f"m-{cid}",
                from_address="a@test.local",
                subject="Test",
                body_text="body",
                received_at=datetime.now(UTC),
                correlation_id=cid,
                account_id=tenant_account_id,
            )
        )
        reviews.upsert_pending(
            correlation_id=cid,
            message_id=f"m-{cid}",
            draft_body="draft",
            grounding_flag=flagged,
            intent="new_booking",
            account_id=tenant_account_id,
        )
        if status == "approved":
            reviews.update_status(
                cid,
                "approved",
                account_id=tenant_account_id,
                approved_body="ok",
            )
            reviews._col.update_one(
                {"_id": cid},
                {"$set": {"grounding_flag": True}},
            )
    resp = client.get("/api/review/ground-zero", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    ids = {item["correlation_id"] for item in data["items"]}
    assert "corr-gz1" in ids
    assert "corr-gz3" in ids
    assert "corr-gz2" not in ids
    assert data["total"] == 2


def test_nav_ground_zero_matches_open_count(
    app: object,
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    mock_db: object,
    email_repo: Any,
) -> None:
    """nav_ground_zero und Ground-Zero-API nutzen dieselbe Zählbasis."""
    from backend.api.services.dashboard_queries import nav_ground_zero

    reviews = ReviewRepository(mock_db)  # type: ignore[arg-type]
    for cid in ("corr-nav-gz1", "corr-nav-gz2"):
        email_repo.upsert_by_message_id(
            StoredEmail(
                message_id=f"m-{cid}",
                from_address="a@test.local",
                subject="Test",
                body_text="body",
                received_at=datetime.now(UTC),
                correlation_id=cid,
                account_id=tenant_account_id,
            )
        )
        reviews.upsert_pending(
            correlation_id=cid,
            message_id=f"m-{cid}",
            draft_body="draft",
            grounding_flag=True,
            intent="new_booking",
            account_id=tenant_account_id,
        )
    ctx = app.extensions["ctx"]  # type: ignore[union-attr]
    open_count = reviews.count_open_grounding(account_id=tenant_account_id)
    assert nav_ground_zero(ctx, tenant_account_id) == open_count
    assert open_count == 2
    resp = client.get("/api/review/ground-zero", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["total"] == open_count


def test_grounding_includes_approved_with_flag(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    mock_db: object,
    email_repo: Any,
) -> None:
    """Freigegeben + grounding_flag erscheint im Grounding-Filter."""
    cid = "corr-g-approved"
    email_repo.upsert_by_message_id(
        StoredEmail(
            message_id="m-g-app",
            from_address="guest@test.local",
            subject="Buchung",
            body_text="buchung",
            received_at=datetime.now(UTC),
            correlation_id=cid,
            account_id=tenant_account_id,
        )
    )
    reviews = ReviewRepository(mock_db)  # type: ignore[arg-type]
    reviews.upsert_pending(
        correlation_id=cid,
        message_id="m-g-app",
        draft_body="draft",
        grounding_flag=True,
        intent="new_booking",
        account_id=tenant_account_id,
    )
    reviews.update_status(
        cid,
        "approved",
        account_id=tenant_account_id,
        approved_body="ok",
    )
    # Legacy: freigegeben, aber Grounding-Flag noch gesetzt (vor Flag-Reset-Fix)
    reviews._col.update_one(
        {"_id": cid},
        {"$set": {"grounding_flag": True}},
    )
    resp = client.get("/api/review/pending?grounding=1", headers=auth_headers)
    assert resp.status_code == 200
    ids = {item["correlation_id"] for item in resp.get_json()["items"]}
    assert cid in ids


def test_pending_grounding_includes_ineligible_booking(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    mock_db: object,
    email_repo: Any,
) -> None:
    """Grounding-Filter zeigt auch Mails, die sonst aus der Queue gefiltert wären."""
    cid = "corr-g-inelig"
    email_repo.upsert_by_message_id(
        StoredEmail(
            message_id="m-inelig",
            from_address="newsletter@spam.local",
            subject="Werbung",
            body_text="unsubscribe",
            received_at=datetime.now(UTC),
            correlation_id=cid,
            account_id=tenant_account_id,
        )
    )
    reviews = ReviewRepository(mock_db)  # type: ignore[arg-type]
    reviews.upsert_pending(
        correlation_id=cid,
        message_id="m-inelig",
        draft_body="draft",
        grounding_flag=True,
        intent="new_booking",
        account_id=tenant_account_id,
    )
    resp = client.get("/api/review/pending?grounding=1", headers=auth_headers)
    assert resp.status_code == 200
    ids = {item["correlation_id"] for item in resp.get_json()["items"]}
    assert cid in ids
