"""Erzeugt Review-Entwürfe für bereits verarbeitete Mails ohne pending Review."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import require_project_venv, safe_print

require_project_venv()

from backend.ai.domain.booking.booking_relevance import effective_booking_intent
from backend.ai.domain.booking.review_eligibility import is_review_queue_eligible
from backend.api.services.review_list_support import workflow_id_for
from backend.core.models.email import ProcessingState


def main() -> int:
    """Erzeugt Review-Entwürfe für verarbeitete Mails ohne pending Review."""
    from backend.core.config.factory import build_app_context
    from backend.core.config.settings import get_settings

    ctx = build_app_context(get_settings())
    wf = ctx.workflow
    limit = 25
    created = 0
    skipped = 0

    states = {
        ProcessingState.VALIDATED.value,
        ProcessingState.RETRIEVED.value,
        ProcessingState.EXTRACTED.value,
        ProcessingState.DRAFTED.value,
    }
    cursor = ctx.email_repo._col.find({"processing_state": {"$in": list(states)}}).sort(
        "updated_at", -1
    )

    for doc in cursor:
        if created >= limit:
            break
        email = ctx.email_repo.get_by_message_id(doc.get("message_id") or doc["_id"])
        if email is None:
            continue
        if ctx.review_repo.get(email.correlation_id) is not None:
            skipped += 1
            continue
        ext = ctx.extraction_repo.get_by_correlation_id(
            email.correlation_id,
            account_id=email.account_id,
        )
        wf_id = workflow_id_for(
            ctx.extraction_repo,
            email.correlation_id,
            account_id=email.account_id or "",
        )
        eligible, _reason = is_review_queue_eligible(
            email,
            ext,
            workflow_id=wf_id,
        )
        if not eligible:
            skipped += 1
            continue
        if effective_booking_intent(email, ext) is None:
            skipped += 1
            continue
        try:
            wf.run(email, thread_id=email.correlation_id)
            created += 1
            safe_print(f"Review-Entwurf: {(email.subject or '')[:50]}")
        except Exception as exc:
            print(f"Fehler {email.correlation_id}: {exc}", file=sys.stderr)

    safe_print(f"Fertig: {created} erstellt, {skipped} uebersprungen (Limit {limit}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
