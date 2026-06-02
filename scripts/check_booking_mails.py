"""List recent booking-related emails and extractions from MongoDB."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from config.settings import get_settings
    from repositories.email_repository import EmailRepository
    from repositories.extraction_repository import ExtractionRepository
    from repositories.mongo import get_database

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    settings = get_settings()
    db = get_database(settings)
    emails = EmailRepository(db)
    extr = ExtractionRepository(db)

    keywords = (
        "buchung",
        "stornierung",
        "booking",
        "beds24",
        "muenzbach",
        "münzbach",
        "änderung",
    )
    print("--- Buchungs-Mails in Mongo (letzte Treffer) ---")
    count = 0
    for doc in emails._col.find().sort("updated_at", -1).limit(300):
        subj = (doc.get("subject") or "").lower()
        if not any(k in subj for k in keywords):
            continue
        cid = doc.get("correlation_id", "")
        ex = extr.get_by_correlation_id(cid)
        intent = ex.intent.value if ex and ex.intent else "-"
        bn = ex.booking_number if ex else "-"
        subject = (doc.get("subject") or "")[:60]
        print(f"intent={intent} booking={bn} | {subject}")
        count += 1
        if count >= 12:
            break

    total = emails._col.count_documents({})
    print(f"\nGesamt E-Mails in DB: {total}, Buchungs-Treffer oben: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
