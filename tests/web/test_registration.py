"""Registrierungs- und Freischaltungs-Tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from models.email import ProcessingState, StoredEmail


def _register_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "email": "neu@test.local",
        "password": "secure-pass",
        "password_confirm": "secure-pass",
        "first_name": "Max",
        "last_name": "Mustermann",
        "phone": "+491701234567",
        "account_type": "private",
    }
    base.update(overrides)
    return base


def test_register_creates_pending_account(client: Any) -> None:
    """Registrierung legt pending Account an, ohne Login."""
    resp = client.post("/api/auth/register", json=_register_payload())
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "pending"
    assert "account_id" in data


def test_register_duplicate_email(client: Any) -> None:
    """Doppelte E-Mail → 409."""
    payload = _register_payload()
    assert client.post("/api/auth/register", json=payload).status_code == 201
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_blocked_until_approved(client: Any) -> None:
    """Pending Account kann sich nicht anmelden."""
    payload = _register_payload(email="pending@test.local")
    client.post("/api/auth/register", json=payload)
    resp = client.post(
        "/api/auth/login",
        json={"email": "pending@test.local", "password": "secure-pass"},
    )
    assert resp.status_code == 403
    assert "Freischaltung" in resp.get_json()["error"]


def test_admin_approve_allows_login(client: Any, auth_headers: dict[str, str]) -> None:
    """Nach Freischaltung ist Login möglich."""
    payload = _register_payload(email="approved@test.local")
    reg = client.post("/api/auth/register", json=payload)
    account_id = reg.get_json()["account_id"]
    approve = client.post(
        f"/api/admin/accounts/{account_id}/approve",
        headers=auth_headers,
    )
    assert approve.status_code == 200
    login = client.post(
        "/api/auth/login",
        json={"email": "approved@test.local", "password": "secure-pass"},
    )
    assert login.status_code == 200
    assert "access_token" in login.get_json()


def test_admin_reject_blocks_login(client: Any, auth_headers: dict[str, str]) -> None:
    """Abgelehnter Account kann sich nicht anmelden."""
    payload = _register_payload(email="rejected@test.local")
    reg = client.post("/api/auth/register", json=payload)
    account_id = reg.get_json()["account_id"]
    client.post(
        f"/api/admin/accounts/{account_id}/reject",
        headers=auth_headers,
        json={"reason": "Unvollständige Angaben"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "rejected@test.local", "password": "secure-pass"},
    )
    assert login.status_code == 403
    assert "abgelehnt" in login.get_json()["error"].lower()


def test_admin_endpoints_require_platform_admin(client: Any) -> None:
    """Normale Nutzer dürfen Freischaltungen nicht sehen."""
    client.post("/api/auth/register", json=_register_payload(email="user@test.local"))
    approve = client.post("/api/admin/accounts/abc/approve")
    assert approve.status_code == 401

    ctx_account = client.post("/api/auth/register", json=_register_payload())
    account_id = ctx_account.get_json()["account_id"]
    client.post(f"/api/admin/accounts/{account_id}/approve", headers={})
    assert client.get("/api/admin/accounts", headers={}).status_code == 401


def test_list_pending_accounts(client: Any, auth_headers: dict[str, str]) -> None:
    """Plattform-Admin sieht pending Accounts."""
    client.post("/api/auth/register", json=_register_payload(email="queue@test.local"))
    resp = client.get("/api/admin/accounts?status=pending", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert any(i["contact_email"] == "queue@test.local" for i in items)


def test_tenant_isolation_between_accounts(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    email_repo: Any,
) -> None:
    """Mails eines anderen Accounts sind für den Admin-Account unsichtbar."""
    email_repo.upsert_by_message_id(
        StoredEmail(
            message_id="other-tenant@test",
            from_address="other@example.com",
            subject="Fremde Mail",
            body_text="secret",
            received_at=datetime.now(UTC),
            correlation_id="corr-other-tenant",
            processing_state=ProcessingState.RECEIVED,
            account_id="other-account-id",
        )
    )
    resp = client.get("/api/emails/", headers=auth_headers)
    assert resp.status_code == 200
    ids = {item["correlation_id"] for item in resp.get_json()["items"]}
    assert "corr-other-tenant" not in ids
