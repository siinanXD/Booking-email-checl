"""Lokaler Demo-Server für README-Screenshots (mongomock, keine Atlas-Verbindung)."""

from __future__ import annotations

import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from flask import Flask
from pymongo.database import Database
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ai.domain.booking.extraction import BookingExtraction  # noqa: E402
from backend.ai.domain.booking.taxonomy import BookingIntent  # noqa: E402
from backend.api.app import create_app  # noqa: E402
from backend.api.auth.token_blocklist import (  # noqa: E402
    InMemoryBlocklistBackend,
    clear_for_tests,
    configure,
)
from backend.core.config.factory import AppContext  # noqa: E402
from backend.core.config.settings import Settings  # noqa: E402
from backend.core.models.email import ProcessingState, StoredEmail  # noqa: E402
from backend.infrastructure.repositories.email_repository import (
    EmailRepository,  # noqa: E402
)
from backend.infrastructure.repositories.extraction_repository import (  # noqa: E402
    ExtractionRepository,
)
from backend.infrastructure.repositories.review_repository import (
    ReviewRepository,  # noqa: E402
)

DEMO_PORT = 5098
ADMIN_EMAIL = "admin@test.local"
ADMIN_PASSWORD = "test-password"
TENANT_EMAIL = "owner-mail@test.local"
TENANT_PASSWORD = "secure-pass"


def _settings() -> Settings:
    return Settings.model_validate(
        {
            "OPENAI_API_KEY": "sk-test",
            "MONGODB_URI": "mongodb://localhost",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "FLASK_SECRET_KEY": "x" * 32,
            "ADMIN_EMAIL": ADMIN_EMAIL,
            "ADMIN_PASSWORD": ADMIN_PASSWORD,
            "WEB_USE_MEMORY_CHECKPOINTER": "true",
            "WEB_DEMO_DATA": "true",
            "LLM_MODE": "mock",
            "FLASK_ENV": "production",
            "APP_ENV": "development",
            "CORS_ORIGINS": f"http://127.0.0.1:{DEMO_PORT}",
            "FRONTEND_BUILD_DIR": "frontend/dist",
        }
    )


def _seed_tenant(flask_app: Flask, ctx: AppContext) -> str:
    from tests.web.test_registration import _register_payload

    client = flask_app.test_client()
    payload = _register_payload(email=TENANT_EMAIL)
    reg = client.post("/api/auth/register", json=payload)
    assert reg.status_code == 201
    reg_json = cast(dict[str, Any], reg.get_json())
    account_id = str(reg_json["account_id"])

    admin_login = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    token = admin_login.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    approve = client.post(
        f"/api/admin/accounts/{account_id}/approve",
        headers=headers,
    )
    assert approve.status_code == 200

    mail_conn = ctx.mail_connection_repo.get_or_create(account_id)
    mail_conn.onboarding_completed = True
    ctx.mail_connection_repo.save(mail_conn)
    return account_id


def _seed_review_item(mock_db: Database[dict[str, Any]], account_id: str) -> None:
    cid = "readme-review-001"
    msg_id = "readme-msg-001@test"
    EmailRepository(mock_db).upsert_by_message_id(
        StoredEmail(
            message_id=msg_id,
            from_address="guest@airbnb.com",
            subject="Neue Buchung AB-2048",
            body_text="Anreise 12.07., 2 Gäste, Apartment Seeblick.",
            received_at=datetime.now(UTC),
            correlation_id=cid,
            processing_state=ProcessingState.PENDING_REVIEW,
            platform="airbnb",
            account_id=account_id,
        )
    )
    ExtractionRepository(mock_db).save(
        cid,
        msg_id,
        BookingExtraction(intent=BookingIntent.NEW_BOOKING, booking_number="AB-2048"),
        account_id=account_id,
    )
    ReviewRepository(mock_db).upsert_pending(
        correlation_id=cid,
        message_id=msg_id,
        draft_body=(
            "Vielen Dank für Ihre Buchung AB-2048. "
            "Wir freuen uns auf Ihren Besuch am 12.07."
        ),
        grounding_flag=False,
        intent="new_booking",
        account_id=account_id,
    )


def build_app(mock_db: Database[dict[str, Any]]) -> Flask:
    configure(InMemoryBlocklistBackend())
    clear_for_tests()
    settings = _settings()
    with patch("backend.core.config.factory.get_database", return_value=mock_db):
        with patch("backend.ai.workflows.checkpointer.build_checkpointer") as mock_cp:
            from langgraph.checkpoint.memory import MemorySaver

            mock_cp.return_value = MemorySaver()
            flask_app = create_app(settings)
            ctx = cast(AppContext, flask_app.extensions["ctx"])
            account = ctx.account_repo.create(
                display_name="Plattform-Administration",
                contact_email=ADMIN_EMAIL,
                account_type="business",
                company_name="Plattform-Administration",
                status="active",
            )
            ctx.user_repo.ensure_platform_admin(
                ADMIN_EMAIL,
                generate_password_hash(ADMIN_PASSWORD),
                account_id=account.id,
            )
            tenant_account_id = _seed_tenant(flask_app, ctx)
            _seed_review_item(mock_db, tenant_account_id)
            return flask_app


def main() -> int:
    import mongomock

    mock_db = cast(
        Database[dict[str, Any]],
        mongomock.MongoClient()["screenshot_demo"],
    )
    app = build_app(mock_db)
    dist = ROOT / "frontend" / "dist"
    if not dist.is_dir():
        print("frontend/dist fehlt — zuerst: cd frontend && npm run build")
        return 1

    server = make_server("127.0.0.1", DEMO_PORT, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Screenshot-Demo: http://127.0.0.1:{DEMO_PORT}")
    print(f"Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"Tenant: {TENANT_EMAIL} / {TENANT_PASSWORD}")
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
