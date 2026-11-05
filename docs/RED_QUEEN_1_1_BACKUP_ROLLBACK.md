# Red Queen 1.1.0 – Sicherung und Rückfall (Produktions-Gate)

**Status: VORBEREITET – keine Produktivfreigabe.**

Dieser Ablauf ist an den am 2026-11-05 per **read-only** geprüften
Produktivserver angepasst. Der Stand 1.0.0 bleibt bis zur ausdrücklichen
Upgradefreigabe unangetastet.

## Produktiver Istzustand (am 2026-11-05 geprüft)

| Merkmal | Beobachtung |
|---|---|
| Docker-Container | `homeassistant` läuft |
| Verwaltung | Docker Compose (Labels im Container) |
| Docker-Image-Referenz | `ghcr.io/home-assistant/home-assistant:stable` |
| Konfigurations-Bind-Mount | `/srv/containers/homeassistant/config:/config`, les- und schreibbar |
| Installierte Red Queen | `manifest.json=1.0.0`, `RELEASE.json=1.0.0` |
| Release-Kanal | `stable` |
| Preflight-Warnungen | Keine |
| Backup/Restore nachgewiesen | **Noch nicht** |
| 1.1.0 installiert | Nein |

## Vorhandenes Backup-System bevorzugen

Auf dem Server wurde zuvor ein Restic-basiertes Server-Backup eingerichtet.
In früheren Ausführungen war `/srv/containers/homeassistant` im Backup-Scope.
Das ersetzt **keinen aktuellen Nachweis**: Vor einer Installation muss
das zuletzt tatsächlich erstellte Snapshot-Datum, dessen Pfad-Inventar,
der Repository-Zustand und die Wiederherstellbarkeit kontrolliert werden.

Read-only Cockpit-Zusammenfassung, soweit das bestehende Kommando installiert ist:

```bash
sudo backup-system --summary
```

Dies ist nur ein Statusaufruf. Keine `forget`, `prune`, `unlock`,
Backup-Rekonfiguration oder USB-Drive-Operation für eine bloße Statusabfrage.
Das Status-Output vor dem Teilen auf private Host-, Repository- oder
Geräteinformationen prüfen.

## Die minimale gesicherte Rückfallbasis

Das Freigabegate muss ausdrücklich alle folgenden Daten abdecken:

1. **Aktive Red Queen 1.0.0** aus
   `/srv/containers/homeassistant/config/custom_components/wnhf`.
2. **Haus- und Registry-Konfiguration**
   `/srv/containers/homeassistant/config/wnhf`, einschließlich etwaiger
   benutzerverwalteter Einstellungen.
3. **Home-Assistant-Persistenz**, insbesondere
   `/srv/containers/homeassistant/config/.storage`. Diese kann
   personenbezogene oder vertrauliche Token enthalten und bleibt lokal.
4. **Aktueller Compose-Startpfad und Docker-Imageidentität**, damit die
   bestehende Laufzeit- und Netzwerkkonfiguration erhalten bleibt.
5. **Nachweislicher Restore-Pfad** aus dem *konkreten* Restic-Snapshot
   in ein getrenntes temporäres Ziel; Version 1.0.0 in den
   wiederhergestellten Dateien prüfen.

Eine aus dem laufenden HA-Verzeichnis gezogene Datei-Kopie der
SQLite-Datenbank ist **kein** nachgewiesenes konsistentes Datenbankbackup.
Bei einem vollständigen Daten- und Integrationsrollback ist vor der
Installation eine geeignete konsistente Sicherung (HA ordnungsgemäß
angehalten oder geeignetes Snapshot-Verfahren) erforderlich.

## Reihenfolge vor einem Produktiv-Upgrade

1. Status `sudo backup-system --summary` **jetzt nur lesen**.
2. Aktuellsten Restic-Snapshot und enthaltene HA-Konfigurationspfade
   im bestehenden Backup-System prüfen; kein neuer freier Backup-Stack.
3. Wiederherstellung eines verifizierten Snapshot-Ausschnitts in ein
   separiertes Testziel nach Sicherheitsfreigabe nachweisen. Keine
   Rücksicherung in `/srv/containers/homeassistant` während HA läuft.
4. Vor der Installation einen aktuellen, konsistenten 1.0.0-Wiederherstellungs-
   punkt herstellen und seine Hashes/Version kontrollieren.
5. Exaktes, SHA-256-geprüftes 1.1.0-Release-Artefakt und Rollback-Paket
   **außerhalb der produktiven Konfiguration** bereitlegen.
6. Erst nach ausdrücklicher Zustimmung das einzelne Red-Queen-
   Integrationsverzeichnis atomar/mit Sicherungswechsel ersetzen,
   bestehende `/config/wnhf` nicht überschreiben.
7. HA ausschließlich mit der *bestehenden* Container-/Compose-Konfiguration
   kontrolliert neu starten – **keinen** neuen Docker-Container mit
   anderen Ports/Volumes als Ersatz aufbauen.
8. Neue Entities/Dashboards/Services überprüfen und die erlaubten
   Einzelfunktionen testen; bei Fehlern vorherige Daten sichern,
   dann in geplantem Wartungsfenster 1.0.0 zurückspielen.

## Rückfallprinzip

**Kein einseitiges Kopieren von nur `manifest.json` oder `const.py`.**
Ein Downgrade verlangt mindestens die vollständigen 1.0.0-
Integrationsdateien. Falls 1.1.0 Persistenz/Registry dauerhaft verändert,
muss der passende konsistente `/config`-Stand restauriert werden.
Vor dem Restore werden die neueren Änderungen lokal gesichert, damit
keine Fehleranalyse verloren geht.

Erst im ausdrücklich freigegebenen Wartungsfenster eine passende
`docker`-Stop-/Restore-/Start-Sequenz verwenden. Ein allgemeines
`docker compose down` ist ausdrücklich **nicht** Teil dieser
Vorgehensweise; es könnte weitere Dienste beeinflussen.

## Sicherheitsgrenze

Dieses Dokument und das zugehörige Preflight führen **keine**
Änderungen am Produktivsystem aus. Nie Backup-Tokens, `.storage`,
Restic-Repository-Passwörter oder Container-Secrets in GitHub,
den Chat oder eine öffentliche CI-Pipeline hochladen.

**NO-GO**, solange aktuelle Snapshot-Abdeckung,
Restorefähigkeit, Upgrade-Prüfungen und ausdrückliche
Installationsfreigabe fehlen.
