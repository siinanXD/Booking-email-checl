"""CLI: ungelesene Outlook-Mails ingestieren (Microsoft Graph)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_VENV_PY = _ROOT / ".venv" / "Scripts" / "python.exe"


def _venv_hint() -> None:
    if not _VENV_PY.exists():
        return
    try:
        if Path(sys.executable).resolve() != _VENV_PY.resolve():
            print(
                "Hinweis: .venv nicht aktiv. Nutze:\n"
                "  .\\.venv\\Scripts\\Activate.ps1\n"
                "  python scripts/run_outlook_ingest.py\n"
                "Oder: .\\scripts\\run_outlook_ingest.ps1",
                file=sys.stderr,
            )
    except OSError:
        return


def _import_error_help(exc: ModuleNotFoundError) -> None:
    print(
        "Import fehlgeschlagen (venv / Pakete fehlen):\n"
        "  py -3.11 -m venv .venv\n"
        "  .\\.venv\\Scripts\\Activate.ps1\n"
        '  pip install -e ".[dev]"\n'
        f"Details: {exc}",
        file=sys.stderr,
    )


_venv_hint()

try:
    from adapters.outlook_ingestion import OutlookIngestionRunner
    from config.factory import build_app_context
    from config.settings import get_settings
except ModuleNotFoundError as exc:
    _import_error_help(exc)
    raise SystemExit(1) from exc

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
