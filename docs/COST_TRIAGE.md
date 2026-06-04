# Triage und API-Kosten

## Ziel

Teure OpenAI-Aufrufe (`classify`, `extract`, `draft`) laufen nur für Mails, die
das vorgeschaltete Triage-Gate passieren. Spam-Erkennung erfolgt **nicht** über
classify/extract, sondern über Regeln und optional ein kleines Triage-Modell.

## Ablauf

1. **Regeln** ([`TriageService`](../backend/ai/services/triage.py)): Blocklist,
   Marketing/Newsletter, Buchungs-Heuristiken, Phishing-Regex.
2. **Unbekannte Absender-Domain**: optional `OPENAI_MODEL_TRIAGE` (`TRIAGE_LLM_ENABLED=true`).
   Ohne LLM: Verwurf wenn keine Buchungs-Keywords im Text (`unknown_domain_no_signals`).
3. **Workflow**: nur `RELEVANT` → `classify` → `extract` → …

## Postfach-Polling

- **Outlook Graph** und **IMAP** lesen nur die **INBOX** (kein Junk/Spam-Ordner).
- Provider-Spamfilter bleibt aktiv; nicht zusätzlich Junk-Folder anbinden.
- `OUTLOOK_FETCH_UNREAD_ONLY=true` reduziert Poll-Last, kann aber bereits gelesene,
  noch nicht verarbeitete Mails überspringen.

## Konfiguration (`.env`)

| Variable | Default | Bedeutung |
|----------|---------|-----------|
| `TRIAGE_LLM_ENABLED` | `true` | LLM-Gate für unbekannte Domains |
| `OPENAI_MODEL_TRIAGE` | `gpt-4o-mini` | Modell für Triage-Gate |
| `TRIAGE_LLM_MAX_BODY_CHARS` | `2000` | Body-Limit im Triage-Prompt |

## Metriken

- Dashboard `spam_discarded_today`: alle `DISCARDED` (Regel + Triage-LLM).
- `MailCostTracker` erfasst auch Triage-LLM-Tokens (vor classify).

## SpamAssassin / EmailVerifier

- **SpamAssassin**: bewusst nicht integriert. Erst prüfen, wenn viel Spam in der
  INBOX ankommt und das Deployment Linux/Docker mit `spamd` erlaubt.
- **EmailVerifier** (SMTP-Deliverability): für **eingehende** Gastmails wenig
  sinnvoll (Relay-Adressen, Mail ist bereits zugestellt). Für späteres
  **ausgehendes** Marketing ggf. separat evaluieren.

## Tests

```bash
pytest tests/test_triage.py tests/test_ingestion_unknown_discard.py tests/test_workflow.py -q
```
