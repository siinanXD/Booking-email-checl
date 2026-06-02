"""CLI: periodisches Mail-Polling (Endlosschleife mit Graceful Shutdown)."""

from __future__ import annotations

import logging
import signal
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "scripts"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

try:
    from run_mail_poll import run_poll

    from backend.core.config.settings import get_settings
except ModuleNotFoundError as exc:
    print(f"Import fehlgeschlagen: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_shutdown = False


def _handle_signal(signum: int, _frame: object) -> None:
    global _shutdown
    logger.info("Received signal %s, shutting down after current run", signum)
    _shutdown = True


def main() -> int:
    """Run the polling loop."""
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    settings = get_settings()
    interval = max(30, settings.mail_poll_interval_seconds)
    logger.info("Mail poll loop started (interval=%ss)", interval)

    while not _shutdown:
        try:
            run_poll()
        except Exception:
            logger.exception("Poll run failed")

        if _shutdown or settings.mail_poll_run_once:
            break

        logger.info("Sleeping %ss until next poll", interval)
        slept = 0
        while slept < interval and not _shutdown:
            time.sleep(min(1, interval - slept))
            slept += 1

    logger.info("Mail poll loop stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
