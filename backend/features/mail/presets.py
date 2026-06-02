"""IMAP-Server-Voreinstellungen für gängige Anbieter."""

from __future__ import annotations

from typing import TypedDict


class ImapPreset(TypedDict):
    label: str
    host: str
    port: int
    use_ssl: bool


IMAP_PRESETS: dict[str, ImapPreset] = {
    "gmx": {
        "label": "GMX",
        "host": "imap.gmx.net",
        "port": 993,
        "use_ssl": True,
    },
    "webde": {
        "label": "Web.de",
        "host": "imap.web.de",
        "port": 993,
        "use_ssl": True,
    },
    "gmail": {
        "label": "Gmail",
        "host": "imap.gmail.com",
        "port": 993,
        "use_ssl": True,
    },
    "outlook_imap": {
        "label": "Outlook.com (IMAP)",
        "host": "outlook.office365.com",
        "port": 993,
        "use_ssl": True,
    },
    "custom": {
        "label": "Eigener IMAP-Server",
        "host": "",
        "port": 993,
        "use_ssl": True,
    },
}
