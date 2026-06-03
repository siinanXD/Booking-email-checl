"""Admin LLM-Konfiguration."""

from __future__ import annotations

from typing import Any


def test_admin_get_llm_config(client: Any, auth_headers: dict[str, str]) -> None:
    resp = client.get("/api/admin/llm-config", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "default_classify_prompt" in data
    assert data["similarity_top_k"] == 3


def test_admin_update_llm_config(
    client: Any,
    auth_headers: dict[str, str],
    app: Any,
) -> None:
    resp = client.put(
        "/api/admin/llm-config",
        headers=auth_headers,
        json={
            "classify_temperature": 0.2,
            "extract_temperature": 0.1,
            "draft_temperature": 0.3,
            "similarity_top_k": 5,
            "classify_prompt_override": "Test {subject}",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["similarity_top_k"] == 5
    assert data["classify_prompt_override"] == "Test {subject}"

    ctx = app.extensions["ctx"]
    saved = ctx.platform_llm_config_repo.get_or_default()
    assert saved.similarity_top_k == 5
    audit = list(ctx.admin_audit_log_repo._col.find())
    assert any(entry.get("action") == "llm_config_update" for entry in audit)


def test_admin_llm_preview_classify(
    client: Any,
    auth_headers: dict[str, str],
) -> None:
    resp = client.post(
        "/api/admin/llm-config/preview",
        headers=auth_headers,
        json={
            "step": "classify",
            "subject": "Neue Buchung AB123",
            "body": "Buchung AB123",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["step"] == "classify"
    assert data["result"] in {
        "new_booking",
        "cancellation",
        "change",
        "guest_inquiry",
        "other",
    }


def test_admin_llm_config_forbidden_for_tenant(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
) -> None:
    resp = client.get("/api/admin/llm-config", headers=tenant_owner_auth_headers)
    assert resp.status_code == 403
