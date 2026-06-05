# Einrichtung für Mandanten (Endnutzer)

## 1. Konto & Postfach

1. Registrierung unter `/register`
2. Onboarding unter `/onboarding` — Outlook OAuth oder IMAP (Presets in der UI)
3. Verbindung testen; bei Fehlern Status unter **Einstellungen → Postfach** prüfen

**Geplant:** Beim ersten Import werden nicht alle alten Mails geladen, sondern nur Nachrichten
ab dem Registrierungszeitpunkt plus die 50 neuesten davor — siehe `docs/ROADMAP.md` Phase 7.

Ausführlich: [`docs/OUTLOOK.md`](OUTLOOK.md)

## 2. E-Mails & Review

- **Dashboard:** KPIs und ausstehende Reviews
- **Listen:** Buchungen, Stornos, Änderungen, Nachrichten (mit Datumsfilter)
- **Review:** Entwurf prüfen, bearbeiten, freigeben — WhatsApp-Vorschau in der Detailansicht
- **Abgeschlossen:** erledigte Reviews unter `/completed`

Es gibt **keinen automatischen E-Mail-Versand** an Gäste nach Freigabe (bewusst Human-in-the-loop).

## 3. Unterkünfte & WhatsApp

**Geplant:** Jahresstatistik (gebuchte Tage, Umsatz), KI-Vorschläge per Klick anlegen,
Profil mit Standort und Kontakt — siehe `docs/ROADMAP.md` Phase 11.

1. **Unterkünfte** (`/properties`): Namen und WhatsApp-Nummern pro Objekt (Putzfrau/Mitarbeiter)
2. **Einstellungen:** globale WhatsApp-Credentials und Standard-Empfänger
3. Bei neuer Buchung: Host + property-spezifische Empfänger (wenn konfiguriert)

Templates: `WHATSAPP_TEMPLATE_*` in der Admin-LLM-/Plattform-Konfiguration.

## 4. Workflows (optional)

Unter **Workflows** Custom-Routing mit Sandbox-Tests. Live-Schaltung erst nach grünen Test-Mails.

Rubriken erscheinen in der Sidebar unter dem Mandanten-Menü.

## 5. Hilfe bei Problemen

- Sync-Fehler: Einstellungen / Dashboard `last_sync_at`
- Keine Review-Einträge: Pipeline-Lauf abwarten oder Admin kontaktieren
- WhatsApp leer: Empfänger unter Unterkünfte + `WHATSAPP_ENABLED=true`
