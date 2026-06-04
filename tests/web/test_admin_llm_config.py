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
    assert data["success"] is True
    assert data["error"] is None
    assert data["result"] in {
        "new_booking",
        "cancellation",
        "change",
        "guest_inquiry",
        "other",
    }


def test_admin_llm_prompt_history_after_updates(
    client: Any,
    auth_headers: dict[str, str],
) -> None:
    first = "Erster Extraktions-Prompt"
    second = "Zweiter Extraktions-Prompt"

    for prompt in (first, second):
        resp = client.put(
            "/api/admin/llm-config",
            headers=auth_headers,
            json={
                "classify_temperature": 0.0,
                "extract_temperature": 0.0,
                "draft_temperature": 0.0,
                "similarity_top_k": 3,
                "extract_prompt_override": prompt,
            },
        )
        assert resp.status_code == 200

    hist = client.get(
        "/api/admin/llm-config/prompt-history/extract",
        headers=auth_headers,
    )
    assert hist.status_code == 200
    data = hist.get_json()
    assert data["prompt_type"] == "extract"
    assert len(data["entries"]) == 2
    assert data["entries"][0]["prompt_text"] == second
    assert data["entries"][1]["prompt_text"] == first


def test_admin_llm_prompt_history_invalid_type(
    client: Any,
    auth_headers: dict[str, str],
) -> None:
    resp = client.get(
        "/api/admin/llm-config/prompt-history/invalid",
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_admin_llm_preview_shows_llm_error(
    client: Any,
    auth_headers: dict[str, str],
    app: Any,
) -> None:
    from unittest.mock import patch

    ctx = app.extensions["ctx"]
    classification = ctx.workflow._nodes._classification  # noqa: SLF001

    def _fail(*_args: object, **_kwargs: object) -> None:
        raise ConnectionError("OpenAI unreachable")

    with patch.object(classification._llm, "complete", side_effect=_fail):
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
    assert data["success"] is False
    assert data["result"] is None
    assert "ConnectionError" in data["error"]
    assert "OpenAI unreachable" in data["error"]


def test_admin_llm_config_forbidden_for_tenant(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
) -> None:
    resp = client.get("/api/admin/llm-config", headers=tenant_owner_auth_headers)
    assert resp.status_code == 403
