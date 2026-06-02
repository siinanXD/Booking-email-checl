"""WSGI entrypoint smoke test."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import mongomock
from langgraph.checkpoint.memory import MemorySaver

from config.settings import Settings
from repositories.mongo import Db


def test_wsgi_module_exposes_flask_app() -> None:
    """WSGI-Modul liefert Flask-App mit funktionierendem /health."""
    settings = Settings.model_validate(
        {
            "OPENAI_API_KEY": "sk-test",
            "MONGODB_URI": "mongodb://localhost",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "FLASK_SECRET_KEY": "x" * 32,
            "WEB_USE_MEMORY_CHECKPOINTER": "true",
            "LLM_MODE": "mock",
        }
    )
    mongo_client: mongomock.MongoClient = mongomock.MongoClient()
    db: Db = mongo_client["wsgi_test"]
    sys.modules.pop("wsgi", None)
    with patch("config.factory.get_database", return_value=db):
        with patch("workflows.checkpointer.build_checkpointer") as mock_cp:
            mock_cp.return_value = MemorySaver()
            with patch("web.app.get_settings", return_value=settings):
                wsgi = importlib.import_module("wsgi")
                client = wsgi.app.test_client()
                resp = client.get("/health")
                assert resp.status_code == 200
                assert resp.get_json()["status"] == "ok"
