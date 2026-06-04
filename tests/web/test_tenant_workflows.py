"""Tenant-Workflows (Phase A, pro Mandant)."""

from __future__ import annotations

from typing import Any


def test_tenant_workflow_duplicate_slug_rejected(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    base = f"/api/admin/accounts/{account_id}/workflows"
    payload = {
        "label": "Workflow Eins",
        "slug": "duplicate_slug",
        "description": "Test",
        "extract_prompt": "Extrahiere JSON: {subject} {body}",
        "sandbox_only": True,
    }
    first = client.post(base, headers=auth_headers, json=payload)
    assert first.status_code == 201
    second = client.post(base, headers=auth_headers, json=payload)
    assert second.status_code == 409


def test_tenant_user_cannot_manage_workflows(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
) -> None:
    """Mandanten-Admins/User: keine Workflow-Verwaltung."""
    create = client.post(
        "/api/workflows",
        headers=tenant_owner_auth_headers,
        json={
            "label": "Forbidden",
            "slug": "forbidden_wf",
            "description": "Test",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
        },
    )
    assert create.status_code == 403
    suggest = client.post(
        "/api/workflows/suggest",
        headers=tenant_owner_auth_headers,
        json={
            "description": "Kaufbestätigungen von Online-Shops erkennen.",
            "label_hint": "Kauf",
        },
    )
    assert suggest.status_code == 403
    listing = client.get("/api/workflows", headers=tenant_owner_auth_headers)
    assert listing.status_code == 403


def test_workflow_nav_lists_only_live(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    client.post(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=auth_headers,
        json={
            "label": "Sandbox WF",
            "slug": "sandbox_only_wf",
            "description": "Nicht in Nav",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
            "enabled": False,
        },
    )
    live = client.post(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=auth_headers,
        json={
            "label": "Live Rubrik",
            "slug": "live_rubrik",
            "description": "Sichtbar in Nav",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
            "enabled": False,
            "test_emails": [{"subject": "T", "body": "Extrahiere strukturierte Daten"}],
            "match_rules": {"subject_keywords": ["live"]},
        },
    )
    assert live.status_code == 201
    live_id = live.get_json()["id"]
    tests = client.post(
        f"/api/admin/accounts/{account_id}/workflows/{live_id}/run-tests",
        headers=auth_headers,
    )
    assert tests.status_code == 200
    assert tests.get_json()["passed"] == tests.get_json()["total"]
    activate = client.put(
        f"/api/admin/accounts/{account_id}/workflows/{live_id}",
        headers=auth_headers,
        json={
            "label": "Live Rubrik",
            "slug": "live_rubrik",
            "description": "Sichtbar in Nav",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": False,
            "enabled": True,
            "test_emails": [{"subject": "T", "body": "Extrahiere strukturierte Daten"}],
            "match_rules": {"subject_keywords": ["live"]},
        },
    )
    assert activate.status_code == 200
    nav = client.get("/api/workflows/nav", headers=tenant_owner_auth_headers)
    assert nav.status_code == 200
    slugs = [item["slug"] for item in nav.get_json()["items"]]
    assert "live_rubrik" in slugs
    assert "sandbox_only_wf" not in slugs


def test_platform_admin_workflow_crud_via_admin_api(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    suggest = client.post(
        f"/api/admin/accounts/{account_id}/workflows/suggest",
        headers=auth_headers,
        json={
            "description": (
                "Kaufbestätigungen von Online-Shops erkennen. "
                "Order-ID und Betrag sind Pflicht."
            ),
            "label_hint": "Kaufbestätigung",
        },
    )
    assert suggest.status_code == 200
    draft = suggest.get_json()
    assert "kauf" in draft["slug"].lower()
    assert "order_id" in draft["required_fields"]

    create = client.post(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=auth_headers,
        json={
            "label": draft["label"],
            "slug": draft["slug"],
            "description": draft["description"],
            "search_hints": draft["search_hints"],
            "importance": draft["importance"],
            "required_fields": draft["required_fields"],
            "optional_fields": draft["optional_fields"],
            "extraction_schema": draft["extraction_schema"],
            "classify_prompt": draft["classify_prompt"],
            "extract_prompt": draft["extract_prompt"],
            "test_emails": draft["test_emails"],
            "match_rules": draft["match_rules"],
            "sandbox_only": True,
            "enabled": False,
        },
    )
    assert create.status_code == 201
    workflow_id = create.get_json()["id"]

    preview = client.post(
        f"/api/admin/accounts/{account_id}/workflows/{workflow_id}/preview",
        headers=auth_headers,
        json={"subject": "Test", "body": "Extrahiere strukturierte Daten"},
    )
    assert preview.status_code == 200
    assert preview.get_json()["success"] is True

    tests = client.post(
        f"/api/admin/accounts/{account_id}/workflows/{workflow_id}/run-tests",
        headers=auth_headers,
    )
    assert tests.status_code == 200
    assert tests.get_json()["total"] >= 1


def test_enable_live_without_tests_rejected(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    create = client.post(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=auth_headers,
        json={
            "label": "Live Workflow",
            "slug": "live_wf",
            "description": "Test",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
            "enabled": False,
            "test_emails": [{"subject": "T", "body": "Extrahiere strukturierte Daten"}],
        },
    )
    assert create.status_code == 201
    workflow_id = create.get_json()["id"]
    update = client.put(
        f"/api/admin/accounts/{account_id}/workflows/{workflow_id}",
        headers=auth_headers,
        json={
            "label": "Live Workflow",
            "slug": "live_wf",
            "description": "Test",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": False,
            "enabled": True,
            "test_emails": [{"subject": "T", "body": "Extrahiere strukturierte Daten"}],
        },
    )
    assert update.status_code == 409


def test_tenant_workflows_isolated_between_accounts(
    client: Any,
    auth_headers: dict[str, str],
    tenant_owner_auth_headers: dict[str, str],
) -> None:
    from tests.web.test_registration import _register_payload

    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    create = client.post(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=auth_headers,
        json={
            "label": "Tenant A Workflow",
            "slug": "tenant_a_only",
            "description": "Isolation test",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
        },
    )
    assert create.status_code == 201
    workflow_id = create.get_json()["id"]

    payload = _register_payload(email="other-tenant@test.local")
    client.post("/api/auth/register", json=payload)
    pending = client.get("/api/admin/accounts?status=pending", headers=auth_headers)
    tenant = next(
        i for i in pending.get_json()["items"] if i["contact_email"] == payload["email"]
    )
    client.post(f"/api/admin/accounts/{tenant['id']}/approve", headers=auth_headers)
    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    other_headers = {"Authorization": f"Bearer {login.get_json()['access_token']}"}

    foreign = client.get(
        f"/api/admin/accounts/{account_id}/workflows/{workflow_id}",
        headers=other_headers,
    )
    assert foreign.status_code == 403
