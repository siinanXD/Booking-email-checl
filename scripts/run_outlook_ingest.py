"""CLI: ungelesene Outlook-Mails ingestieren (Microsoft Graph)."""

from __future__ import annotations

import logging
import sys

from adapters.outlook_ingestion import OutlookIngestionRunner
from config.factory import build_app_context
from config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run the command workflow."""
    settings = get_settings()
    mode = settings.llm_mode.strip().lower()
    logger.info(
        "LLM_MODE=%s, OUTLOOK_FETCH_MAX=%s, unread_only=%s",
        mode,
        settings.outlook_fetch_max,
        settings.outlook_fetch_unread_only,
    )
    if mode == "mock":
        logger.warning(
            "LLM_MODE=mock: Klassifikation/Extraktion/Draft sind Platzhalter, "
            "keine echte KI-Qualitaet."
        )
    elif mode == "live":
        logger.info("LLM_MODE=live: OpenAI-API wird genutzt (Guthaben noetig).")
    ctx = build_app_context(settings)
    runner = OutlookIngestionRunner.from_context(settings, ctx)
    result = runner.run()
    for item in result.items:
        if item.error:
            logger.error(
                "message_id=%s graph_id=%s error=%s",
                item.message_id,
                item.graph_id,
                item.error,
            )
        elif item.skipped_existing:
            logger.info("skip existing message_id=%s", item.message_id)
        elif item.duplicate:
            logger.info("duplicate message_id=%s", item.message_id)
        else:
            logger.info("ingested message_id=%s", item.message_id)
    logger.info("Done: %s new ingest(s)", result.processed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
