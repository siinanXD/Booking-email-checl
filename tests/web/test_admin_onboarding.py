"""Plattform-Admin: kein Mail-Onboarding."""

from __future__ import annotations

from typing import Any

from tests.web.test_registration import _register_payload


def test_platform_admin_me_skips_mail_onboarding(
    client: Any,
    auth_headers: dict[str, str],
) -> None:
    """Plattform-Admin hat mail_onboarding_completed=true ohne Postfach."""
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["role"] == "platform_admin"
    assert data["mail_onboarding_completed"] is True


def test_admin_me_endpoint(client: Any, auth_headers: dict[str, str]) -> None:
    """GET /api/admin/me liefert Admin-Kontext."""
    resp = client.get("/api/admin/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["role"] == "platform_admin"
    assert data["mail_onboarding_required"] is False


def test_admin_me_forbidden_for_tenant(
    client: Any,
    auth_headers: dict[str, str],
) -> None:
    """Freigeschaltete Mandanten dürfen /api/admin/me nicht aufrufen."""
    payload = _register_payload(email="tenant-me@test.local")
    client.post("/api/auth/register", json=payload)
    account_id = client.get("/api/admin/accounts?status=pending", headers=auth_headers)
    tenant = next(
        i
        for i in account_id.get_json()["items"]
        if i["contact_email"] == payload["email"]
    )
    client.post(f"/api/admin/accounts/{tenant['id']}/approve", headers=auth_headers)
    tenant_login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    tenant_headers = {
        "Authorization": f"Bearer {tenant_login.get_json()['access_token']}"
    }
    resp = client.get("/api/admin/me", headers=tenant_headers)
    assert resp.status_code == 403
