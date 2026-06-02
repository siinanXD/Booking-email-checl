#!/usr/bin/env python3
"""Cursor beforeShellExecution-Hook: blockiert riskante Git-Befehle.

Dieser Hook ist die technische Durchsetzung deiner Regel "kein Direkt-Push auf
main". Cursor reicht den geplanten Shell-Befehl als JSON auf stdin; wir
antworten mit JSON auf stdout. Ein Feld 'permission' bzw. 'continue' steuert,
ob Cursor den Befehl ausführt. Bei Verstoessen geben wir 'deny' zurueck.

Hinweis: Cursor Hooks sind Beta. Das genaue Antwortschema (z. B. 'permission'
vs. 'continue') kann sich aendern – gegen die aktuelle Cursor-Doku pruefen.
Faellt der Hook aus, blockieren wir im Zweifel NICHT (fail-open), damit die
Arbeit nicht stehenbleibt; die harte Schranke bleibt ohnehin der serverseitige
Branch-Schutz auf 'main'.
"""
from __future__ import annotations

import json
import re
import sys

# Muster, die wir niemals automatisch ausfuehren lassen wollen.
BLOCKED_PATTERNS = [
    r"\bgit\s+push\b.*\bmain\b",        # direkter Push nach main
    r"\bgit\s+push\b.*\borigin\s+main", # explizit origin main
    r"\bgit\s+push\s+--force\b",        # Force-Push generell
    r"\bgit\s+push\s+-f\b",
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Kein verwertbarer Input -> nicht blockieren (fail-open).
        print(json.dumps({"permission": "allow"}))
        return 0

    command = str(payload.get("command", ""))

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            # 'deny' weist Cursor an, den Befehl nicht auszufuehren.
            print(
                json.dumps(
                    {
                        "permission": "deny",
                        "userMessage": (
                            "Direkter Push/Force-Push auf 'main' ist gesperrt. "
                            "Nutze einen Feature-Branch und einen PR mit gruener CI."
                        ),
                    }
                )
            )
            return 0

    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
