"""IMAP-Autodiscovery: lokale Presets → Mozilla ISPDB Fallback."""

from __future__ import annotations

import logging
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from backend.features.mail.presets import IMAP_PRESETS, find_preset_by_domain

logger = logging.getLogger(__name__)

_ISPDB_URL = "https://autoconfig.thunderbird.net/v1.1/{domain}"
_TIMEOUT_SECONDS = 4


def autodiscover_imap_config(domain: str) -> dict | None:
    """Gibt IMAP-Konfiguration für eine Domain zurück oder None.

    Reihenfolge:
    1. Lokale Voreinstellungen (kein externer Aufruf)
    2. Mozilla ISPDB (nur Domain wird übertragen, kein Passwort o.Ä.)
    """
    # 1. Lokale Presets
    preset_id = find_preset_by_domain(domain)
    if preset_id and preset_id != "custom":
        preset = IMAP_PRESETS[preset_id]
        return {
            "preset_id": preset_id,
            "label": preset["label"],
            "host": preset["host"],
            "port": preset["port"],
            "use_ssl": preset["use_ssl"],
            "source": "local",
        }

    # 2. Mozilla ISPDB
    try:
        url = _ISPDB_URL.format(domain=domain)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AI-Mail-Platform/1.0 (IMAP autodiscover)"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            tree = ET.parse(resp)
            root = tree.getroot()

        imap_el = root.find(".//incomingServer[@type='imap']")
        if imap_el is None:
            return None

        hostname = (imap_el.findtext("hostname") or "").strip()
        port_raw = (imap_el.findtext("port") or "993").strip()
        socket_type = (imap_el.findtext("socketType") or "SSL").strip().upper()

        if not hostname:
            return None

        try:
            port = int(port_raw)
        except ValueError:
            port = 993

        # Nur echte TLS-Verbindungen akzeptieren (kein Plaintext port 143)
        use_ssl = socket_type in ("SSL", "STARTTLS")
        if not use_ssl or port == 143:
            logger.warning(
                "ISPDB für %s schlug unverschlüsselte Verbindung vor – ignoriert.",
                domain,
            )
            return None

        return {
            "preset_id": "custom",
            "label": domain,
            "host": hostname,
            "port": port,
            "use_ssl": True,
            "source": "ispdb",
        }

    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.debug("ISPDB: kein Eintrag für %s", domain)
        else:
            logger.warning("ISPDB HTTP-Fehler für %s: %s", domain, exc)
    except TimeoutError:
        logger.warning("ISPDB Timeout für %s", domain)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ISPDB unerwarteter Fehler für %s: %s", domain, exc)

    return None
