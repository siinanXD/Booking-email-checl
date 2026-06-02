# Microsoft Graph / Outlook Ingestion

Dieses Projekt liest eingehende Mails über die Microsoft Graph API und startet
den bestehenden `EmailWorkflow` (inkl. Human Review – kein Auto-Versand).

## Entra (Azure AD) App

1. **App-Registrierung** anlegen.
2. **Delegated** (Entwicklung / privates Hotmail):
   - API permissions: `Mail.Read`, `User.Read` (delegated)
   - „Accounts in any organizational directory and personal Microsoft accounts“
   - „Allow public client flows“ = Yes
3. **Application** (Shared Mailbox / Hintergrund):
   - API permission: `Mail.Read` (application)
   - Admin consent
   - Client secret anlegen
   - `OUTLOOK_MAILBOX` = UPN oder SMTP der Mailbox

## Auth-Modi

| Modus | Env | Graph-Pfad |
|-------|-----|------------|
| `delegated` (Default) | `AZURE_CLIENT_ID`, optional `AZURE_AUTHORITY=common` | `/me/...` |
| `application` | + `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`, `OUTLOOK_MAILBOX` | `/users/{mailbox}/...` |

Delegated nutzt **Device Code** und speichert Tokens in
`.outlook_token_cache.json` (gitignored). MSAL speichert Refresh-Token automatisch
(`offline_access` wird intern ergänzt, nicht in `DELEGATED_SCOPES` eintragen).

- **Erster Lauf** (oder nach Cache-Löschung): URL + Code in der Konsole, einmal anmelden.
- **Weitere Läufe** mit `python scripts/run_outlook_ingest.py`: **kein** erneuter Login,
  solange die Datei `.outlook_token_cache.json` existiert (Log: `Anmeldung aus Token-Cache`).

**Ohne User-Login (Produktion):** `OUTLOOK_AUTH_MODE=application` + Secret + Shared Mailbox.

Schnelltest Graph (PowerShell, **ohne** Token-Cache – jedes Mal Device Code):  
`.\scripts\test_graph_mailbox_delegated.ps1`

## Umgebungsvariablen

Siehe `.env.example` (Abschnitt Microsoft Graph). Pflicht für Ingest zusätzlich
zu OpenAI/Mongo/Langfuse: mindestens `AZURE_CLIENT_ID`. Bei
`OUTLOOK_AUTH_MODE=application` auch Tenant, Secret und Mailbox.

Optional:

- `OUTLOOK_POST_ACTION=none` (Default, nur lesen mit `Mail.Read`) oder `mark_read` / `move`
  (`mark_read`/`move` brauchen **Mail.ReadWrite** in Entra + erneute Zustimmung)
- `OUTLOOK_PROCESSED_FOLDER` (bei `move`)
- `OUTLOOK_TOKEN_CACHE_PATH` (Default: `.outlook_token_cache.json`)

## OpenAI-Guthaben umgehen (nur Entwicklung)

**ChatGPT Pro** gilt nicht für die API. Ohne Guthaben auf [platform.openai.com](https://platform.openai.com)
scheitert `LLM_MODE=live` mit `insufficient_quota`.

Für Tests ohne API-Kosten in `.env`:

```env
LLM_MODE=mock
```

Dann laufen Klassifikation, Extraktion, Embeddings und Draft mit **Mock-Antworten**
(wie in `pytest`). Qualität ist nicht produktiv — nur Pipeline-Verdrahtung.

## Ingest ausführen

```powershell
cd C:\Users\sinan\CursorProjekt\Booking-email-checl
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python scripts/run_outlook_ingest.py
```

Ohne `Activate` (nutzt automatisch `.venv`):

```powershell
.\scripts\run_outlook_ingest.ps1
```

**Nicht** das globale `python` von Windows — sonst: `No module named 'adapters'` oder `msal`.

Ablauf: neueste Inbox-Mails (Standard: **100**, `OUTLOOK_FETCH_MAX`) →
`IncomingEmail` → `workflow.run()` → bei Erfolg als gelesen markieren (oder
verschieben). Bereits bekannte `message_id` (Mongo Dedup) werden übersprungen.

Standard: die **100 neuesten** Mails im Posteingang (`OUTLOOK_FETCH_UNREAD_ONLY=false`).
Nur ungelesene: `OUTLOOK_FETCH_UNREAD_ONLY=true` (trotzdem max. 100).

## Tests

Unit-Tests mit gemockten Graph-JSON (kein Live-API in CI):

```bash
pytest tests/test_outlook_graph.py -q
```

Live-Test (manuell): `pytest -m live_graph` (nur mit gültiger `.env`).
