# Red Queen 1.1.0 – Release-Gate und kontrollierter Produktivtest

**Status: NO-GO – dieser Entwicklungsbranch darf nicht als Produktivrelease installiert werden.**

## Architekturentscheidung

- 13 bereits vom Anlagenbetreiber erprobte DALI-RGBW-Lichter werden als vorhandene asyncua-Light-Entitäten übernommen. Keine doppelten native WNHF-RGBW-Lichter.
- Einzelne Leuchten werden weiterhin direkt über Home Assistant/OPC UA bedient. Red Queen ersetzt keinen PLC-/DALI-Treiber.
- Batch-Lichtszenen sind nur bei Hausmodus home und verifiziert deaktiviertem Ruhemodus zugelassen, unabhängig davon, ob ein HA-Service, Automation oder Button die Szene auslöst.
- Manuelles Ein-/Ausschalten/Farbwechseln einer einzelnen vorhandenen Leuchte bleibt möglich.
- Neue Smart-Living-TTS-Profile voice und broadcast haben dieselben Hausmodus-/Ruhemodus-Sperren. Ohne verifizierte Ruhestellung (binary_sensor = off) wird keine neue Komfort-Durchsage ausgelöst.
- Mobile Smart-Living-Mitteilungen bleiben bei away, vacation und quiet verfügbar.
- Bestehende Red-Queen-1.0 Benachrichtigungsautomationen (auch bisherige explizite broadcast-/Alarm-Ausnahmen) bleiben unverändert. Das ist eine Kompatibilitätsentscheidung; keine Behauptung eines globalen Durchsagen-Schutzes für alle HA-Service-Aufrufer.
- Neue Hausmodi sind zunächst manuell, auto_away ist standardmäßig false.

## Bereits belegte Abnahme

- Isolierter HA-Starttest des Entwicklungscommits db37a04: PASS; fünf native Smart-Living-Entitäten angelegt, keine Fehler im kompakten Bericht.
- 13 von 13 DALI-Quellen zeigen native HA-Fähigkeit ColorMode.RGBW; der Anlagenbetreiber bestätigt Funktion von Farben und Helligkeit im Praxisbetrieb.
- GitHub-Workflows validieren Python/Unit- und Strukturverträge sowie hassfest automatisch. Diese Kontrollen ersetzen kein real angeschlossenes HA.

## Gate A – automatisierte Entwicklungstests

- Auf dem finalen Release-Kandidaten müssen beide GitHub-Workflows (Static repository checks und hassfest) erfolgreich sein.
- Unit-Testmatrix: home/away/vacation, Ruhemodus on/off/missing/unknown, Smart-Living broadcast/voice/mobile, Legacy-Broadcast kompatibel.
- Szenen-Guard darf weder via Serviceparameter noch via button.press umgangen werden.
- Keine alten WNHF-Licht-IDs entfernen, keine doppelten neuen RGBW-Proxy-Entitäten einführen.
- Versions- und Checksum-Katalog für 1.1.0 erstellen, ohne den Stable-1.0.0-Validator zu verändern.

## Gate B – isolierter Home-Assistant-Starttest

- Das bereits genutzte isolierte Staging-Skript auf den tatsächlichen finalen Entwicklungscommit ausrichten und erneut ausführen.
- Die aktuelle, neue 1.1-Codebasis muss mit derselben HA-Version starten; sowohl neue HA-Entitäten als auch bestehende semantische Entitäten kontrollieren.
- Kein Netzwerkzugriff oder externe WAGO-/Sonos-Aufrufe, keine physischen Schaltbefehle.
- Neu hinzugefügte Smart-Living-Services und Nachrichtenpfade ohne reale Empfänger in sicherer Testumgebung überprüfen.

## Gate C – Vorbereitung des kontrollierten Produktivupgrades

- Versionsstand von HA und Red Queen 1.0.0 erneut abgleichen.
- **Vor der Installation ein nachweislich rückspielbares Backup** der HA-Konfiguration, Integrationsdateien, Registry, Einstellungen und relevanter Persistenz anlegen; idealerweise vorhandene Restic-Sicherung prüfen. Live-SQLite/Recorder-Daten nicht mit ungesicherten Dateikopien als konsistentes Backup behandeln.
- Exakte 1.0.0-Integrationsdateien/Release-Artefakte und dokumentierte Rückkehrprozedur bereithalten.
- HACS-/Home-Assistant-Versionen und HA-Neustartfenster festlegen; Red Queen 1.1 manifestieren und versioniert freigeben.
- Nur nach ausdrücklicher Entscheidung des Anlagenbetreibers in der Produktion installieren.

## Gate D – Praxistest nach Upgrade (gemeinsam)

1. Red Queen startet, Registry/Services/Dashboards und bestehende WAGO-Taster funktionieren unverändert.
2. Alle 13 bisherigen DALI-Entitäten sind weiterhin vorhanden; keine neuen wnhf_rgbw-Entitäten. Das Smart-Living-Dashboard zeigt sie direkt.
3. Hausmodus home/away/vacation: manueller Wechsel und Persistenz nach Testneustart.
4. Eine Testszene nur in home + quiet off, Abbruch in away/vacation/quiet; keine spontane Szenenaktivierung beim Setup.
5. Eine harmlose Sonos-Testnachricht in home + quiet off nach Betreiberfreigabe, danach verifizierte Sperre in away/vacation/quiet.
6. Mobile Testnachricht und bestehende Alarm-/Benachrichtigungswege getrennt prüfen, ohne reale Notfallalarme auszulösen.
7. Protokolle und Verfügbarkeit checken; bei Fehlern sofort auf dokumentierten 1.0.0-Stand zurückrollen.

## Wichtige Trennung der Nachweise

**CI PASS** = statische und unitbasierte Quellcodeprüfung.
**STAGING PASS** = Home Assistant hat unter Isolation initialisiert und Entitäten registriert.
**Praxistest PASS** = gemeinsam am angeschlossenen Produktivsystem nach Upgrade überprüft.

Keiner dieser Nachweise impliziert automatisch die anderen. Bis zur abschließenden
Freigabe bleibt Pull Request #2 ein Draft und Red Queen 1.0.0 produktiv.
