"""Tests für LangfuseWipeService (DSGVO-Trace-Löschung)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from backend.infrastructure.observability.langfuse_wipe import LangfuseWipeService


def test_no_credentials_returns_zero() -> None:
    """Ohne Credentials werden keine Traces gelöscht."""
    svc = LangfuseWipeService(public_key=None, secret_key=None)
    result = svc.delete_traces_for_sessions(["corr-1", "corr-2"])
    assert result == 0


def test_empty_session_list_returns_zero() -> None:
    """Leere Liste → keine API-Calls, 0 zurück."""
    svc = LangfuseWipeService(public_key="pub", secret_key="sec")
    result = svc.delete_traces_for_sessions([])
    assert result == 0


def test_deletes_traces_for_each_session() -> None:
    """Für jede session_id werden fetch + delete aufgerufen."""
    mock_trace_1 = MagicMock()
    mock_trace_1.id = "trace-abc"
    mock_trace_2 = MagicMock()
    mock_trace_2.id = "trace-def"

    mock_fetch_result = MagicMock()
    mock_fetch_result.data = [mock_trace_1]
    mock_fetch_result_2 = MagicMock()
    mock_fetch_result_2.data = [mock_trace_2]

    mock_client = MagicMock()
    mock_client.fetch_traces.side_effect = [mock_fetch_result, mock_fetch_result_2]

    svc = LangfuseWipeService.__new__(LangfuseWipeService)
    svc._client = mock_client

    result = svc.delete_traces_for_sessions(["session-1", "session-2"])

    assert result == 2
    assert mock_client.fetch_traces.call_count == 2
    assert mock_client.client.trace.delete.call_count == 2
    mock_client.client.trace.delete.assert_any_call(trace_id="trace-abc")
    mock_client.client.trace.delete.assert_any_call(trace_id="trace-def")


def test_fetch_error_is_swallowed() -> None:
    """API-Fehler beim Fetch werden geloggt, kein Exception nach oben."""
    mock_client = MagicMock()
    mock_client.fetch_traces.side_effect = RuntimeError("Netz-Fehler")

    svc = LangfuseWipeService.__new__(LangfuseWipeService)
    svc._client = mock_client

    result = svc.delete_traces_for_sessions(["session-x"])
    assert result == 0  # Fehler → 0, kein Absturz


def test_delete_error_counts_partial() -> None:
    """Einzelne Delete-Fehler werden übersprungen, Rest zählt."""
    mock_trace_ok = MagicMock()
    mock_trace_ok.id = "trace-ok"
    mock_trace_fail = MagicMock()
    mock_trace_fail.id = "trace-fail"

    mock_fetch_result = MagicMock()
    mock_fetch_result.data = [mock_trace_ok, mock_trace_fail]

    mock_client = MagicMock()
    mock_client.fetch_traces.return_value = mock_fetch_result

    def _delete(trace_id: str) -> None:
        if trace_id == "trace-fail":
            raise RuntimeError("Löschen fehlgeschlagen")

    mock_client.client.trace.delete.side_effect = _delete

    svc = LangfuseWipeService.__new__(LangfuseWipeService)
    svc._client = mock_client

    result = svc.delete_traces_for_sessions(["session-1"])
    assert result == 1  # nur trace-ok gezählt


def test_wipe_account_includes_langfuse_count() -> None:
    """DataWipeService.wipe_account liefert langfuse_traces in counts."""
    import mongomock

    from backend.features.platform.data_wipe_service import DataWipeService

    db: Any = mongomock.MongoClient()["testdb"]
    db["emails"].insert_one({"_id": "corr-1", "account_id": "acc-123"})

    mock_lf = MagicMock(spec=LangfuseWipeService)
    mock_lf.delete_traces_for_sessions.return_value = 3

    svc = DataWipeService(db, langfuse_wipe=mock_lf)
    counts = svc.wipe_account("acc-123")

    assert counts.get("langfuse_traces") == 3
    mock_lf.delete_traces_for_sessions.assert_called_once_with(["corr-1"])
