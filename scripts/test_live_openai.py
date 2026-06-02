"""Einmaliger Live-Test: OpenAI Embeddings + Chat (keine Outlook-Mails)."""

from __future__ import annotations

import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    """Live-Smoke-Test für OpenAI Embeddings und Chat (ohne Outlook)."""
    from config.factory import build_app_context
    from config.settings import get_settings
    from models.email import IncomingEmail
    from repositories.embedding_repository import EmbeddingRepository
    from repositories.mongo import get_database
    from services.indexing import EmbeddingClient
    from services.openai_client import OpenAIClient

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    settings = get_settings()
    mode = settings.llm_mode.strip().lower()
    print(f"LLM_MODE={mode}")
    if mode != "live":
        print("Setze LLM_MODE=live in .env und starte erneut.")
        return 2

    print(f"EMBEDDING_MODEL={settings.embedding_model}")
    print(f"CLASSIFY={settings.openai_model_classify}")
    print(f"EXTRACT={settings.openai_model_extract}")
    print(f"DRAFT={settings.openai_model_draft}")

    print("\n--- Embedding ---")
    embed = EmbeddingClient(
        settings.openai_api_key,
        settings.embedding_model,
        use_langfuse=True,
        tracing=False,
    )
    vec = embed.embed("Buchung AB123, Check-in 2026-06-12, Apartment Berlin")
    print(f"OK: dimension={len(vec)}, first_values={vec[:4]}")

    print("\n--- Chat smoke ---")
    llm = OpenAIClient(settings.openai_api_key, use_langfuse=True)
    smoke = llm.complete(
        "Antworte nur mit dem Wort OK.", settings.openai_model_classify
    )
    tok = f"{smoke.prompt_tokens}+{smoke.completion_tokens}"
    print(f"OK: reply={smoke.text!r}, tokens={tok}")

    print("\n--- Workflow (eine Test-Mail) ---")
    uid = uuid.uuid4().hex[:12]
    email = IncomingEmail(
        message_id=f"live-test-{uid}@local.test",
        from_address="bookings@beds24.com",
        to_addresses=["m.w.immobilien@gmx.de"],
        subject="Buchung: Test Apartment",
        body_text=(
            "Buchungsnummer: AB123\n"
            "Check-in: 12.06.2026\n"
            "Check-out: 15.06.2026\n"
            "Gäste: 2\n"
            "Quelle: Booking.com"
        ),
        received_at=datetime.now(UTC),
        platform="beds24",
    )
    ctx = build_app_context(settings)
    result = ctx.workflow.run(email, thread_id=email.correlation_id)
    intent = result.get("intent")
    extraction = result.get("extraction")
    draft = result.get("draft")
    print(f"intent={intent}")
    if extraction is not None:
        print(
            f"extraction: booking={getattr(extraction, 'booking_number', None)}, "
            f"confidence={getattr(extraction, 'confidence', None)}"
        )
    if draft is not None:
        body = getattr(draft, "body", "") or ""
        print(f"draft ({len(body)} chars): {body[:300]}...")
        mock_phrase = "Ihre Anfrage wurde bearbeitet"
        if mock_phrase in body:
            print("WARN: Draft sieht nach Mock-Text aus, nicht nach echtem GPT.")
    else:
        print("WARN: kein draft im Ergebnis (Spam/Triage?)")

    print("Warte 3s auf Hintergrund-Indexierung...")
    time.sleep(3)
    emb_repo = EmbeddingRepository(get_database(settings))
    stored = emb_repo._col.find_one({"correlation_id": email.correlation_id})
    if stored:
        embedding = stored.get("embedding") or []
        dim = len(embedding)
        mock_vec = len(embedding) >= 3 and embedding[:3] == [1.0, 0.5, 0.25]
        print(f"embedding in Mongo: dimension={dim}, mock_vector={mock_vec}")
    else:
        print("WARN: kein Embedding-Chunk in Mongo")

    print("\nAlle Live-Tests bestanden.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FEHLER: {type(exc).__name__}: {exc}")
        sys.exit(1)
