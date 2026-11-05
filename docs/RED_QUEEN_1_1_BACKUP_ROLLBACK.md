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

## Lesender Backup-Cockpit-Befund vom 05.11.2026, 20:38 CET

Der Betreiber führte `sudo backup-system --summary` erfolgreich aus:

- Server: `weidnerhome-srv2`
- Tägliches Backup: `active`, Backup-Watchdog: `active`
- Retention-V3-Timer: `active/enabled`
- Produktiver Freigabemarker: vorhanden
- Einmalige Plan-Autorisierung: fehlt; dies ist **keine** Freigabe für einen neuen Retention-Plan
- Letzter Backup-Dienst: `success`
- Letzter Retention-Dienst: `success` (01.11.2026, 04:39 CET)
- USB 1: offline/ausgehängt, ausdrücklich **normaler Sollzustand**
- Snapshot-Zahlen: nicht live abgefragt, weil das USB-Repository offline bleibt

**Einordnung:** Dies ist ein positiver Dienststatus, aber **noch kein**
Nachweis des letzten Snapshot-Datums, der tatsächlich abgedeckten
Home-Assistant-Verzeichnisse oder eines erfolgreichen Restore-Tests.
Bis dahin bleibt die Produktivfreigabe gesperrt. USB nicht ungefragt
mounten, kein Restic-Write, kein `forget`/`prune`/`unlock`.

## Erfolgreicher Backup-Dienst vom 05.11.2026

Der Betreiber hat die Ausgaben von `systemctl show` und
`journalctl -u weidnerhome-server-backup.service -n 60`
zur Verfügung gestellt. Sie bestätigen:

- `Result=success`, `ExecMainStatus=0`
- Laufzeit: **05.11.2026 03:33:16 bis 03:35:36 CET**
- Im protokollierten Backup-Dateibaum enthalten:
  `/srv/containers/homeassistant` (neben `/srv/containers/dokuwiki` usw.).
- Ausgabe am Laufende: `12 snapshots`.
- `Server Backup erfolgreich abgeschlossen`, anschließend
  `Starte Home Assistant...`, `Starte DokuWiki...`,
  `Synchronisiere Dateisystem...`.
- `PASS: USB 1 wieder offline` – erwarteter Schutzbetrieb.
- Retention ist während des Tagesbackups deaktiviert und erfolgt
  ausschließlich über die separate Wartung.

**Grenze des Nachweises:** Die 60 letzten Journalzeilen enthalten kein
eindeutiges Snapshot-ID-/Datum-Mapping und keine Restic-
`ls`-/Restore-Prüfung des konkreten 05.11-Snapshots. Das
`12 snapshots`-Ergebnis belegt nur eine im Backup-Lauf
ausgegebene Anzahl, keine Wiederherstellungsprobe. Die tatsächliche
Wiederanlaufbereitschaft nach HA-Neustart wurde nicht gesondert
geprüft. Kein USB-Mount zur bloßen Statusauswertung.

**Nächster sicherer Schritt:** Ohne Mount oder Restic-Write zuerst
gezielte Journalzeilen des Laufzeitfensters auf das Snapshot-ID-Mapping
prüfen. Falls das nicht reicht, benötigt ein gesonderter Restore-Drill
eine bewusst freigegebene, ausschließlich lesende temporäre
Repository-Verfügbarkeit. Keine produktiven Daten überschreiben.

## Konkreter Snapshot des Tagesbackups 05.11.2026

Die gezielte reine Journalabfrage hat folgende Meldungen bestätigt:

- Vor Snapshot-Erstellung: `Stoppe Home Assistant...` und `Stoppe DokuWiki...`.
- Restic hat Snapshot `2bf78693` gespeichert, basierend auf Elternsnapshot `20e88793`.
- Verarbeitungsumfang: `12146 files`, `2.355 GiB`, Restic-Verarbeitungsdauer `1:57`.
- Die Sicherungsübersicht nennt `/srv/containers/homeassistant` als Sicherungswurzel.
- Das Tagesbackup meldet insgesamt `12 snapshots` und `Server Backup erfolgreich abgeschlossen`.
- Danach folgen `Starte Home Assistant...`, `Starte DokuWiki...` und `PASS: USB 1 wieder offline`.

**Beweisniveau:** Der Backupdienst wurde für den Snapshot kontrolliert angehalten,
der Snapshot `2bf78693` wurde gespeichert und der Datenträger wurde sicher
ausgehängt. Ein erfolgreiches `restic ls` bzw. `restic restore` auf diesen
Snapshot ist **noch nicht** nachgewiesen. Ebenso muss der tatsächliche
Home-Assistant-Wiederanlauf separat geprüft werden. Die Backupaufnahme
um 03:33 kann spätere Änderungen vom selben Tag nicht abdecken; vor dem
Upgrade ist ein zeitnaher neuer konsistenter Sicherungspunkt vorzusehen.

**Nächster Schritt:** Architektur des vorhandenen Backup-Dienstes bzw.
des Backup-Cockpits nur lesend prüfen, anschließend einen separaten Restore-
Drill mit ausdrücklicher Mount-/Schreibziel-Freigabe durchführen. Keine
unautorisierte USB-Mountaktion, kein Schreiben in das bestehende Repository.

## Wiederherstellungsunterlagen und Mountstatus (05.11.2026, Abend)

Die reine Bestandsabfrage des Betreibers hat ergeben:

- `findmnt --mountpoint /srv/storage/network_drive_1`: kein Dateisystem an **diesem geprüften Pfad** eingehängt.
- Unter `/srv/admin/server-docs/recovery/server-restic-maintenance/` sind unter anderem `WATCHDOG-RECOVERY.txt`, `RETENTION-V3-RECOVERY.txt`, `MAINT-TIMER-RECOVERY.txt` und `ALARM-RECOVERY.txt` auffindbar.
- Ein spezifisch benanntes Home-Assistant-Restic-Restore-Handbuch wurde mit der begrenzten Dateinamenssuche noch nicht gefunden.
- **Wichtig:** Der im vorigen Diagnosebefehl geprüfte Mountpoint ist nicht durch einen Abgleich mit `/usr/local/sbin/server-backup` verifiziert. Keine Behauptung, dass dies der echte USB-1-Mountpoint ist.

Vor einem Restore zunächst **nur lesend** die physische Datenträgerzuordnung
(`lsblk`, `findmnt -S /dev/sdb1`) und die tatsächlich konfigurierte
Mount-/Repository-Verwendung im Produktiv-Sicherungsskript ermitteln.
Da Journal-Meldungen `/dev/sdb1` nennen, ist dieser Name nur eine
**Momentaufnahme** und kein dauerhaftes Identifikationsmerkmal; für die
spätere Recovery bevorzugt UUID/PARTUUID prüfen.

Es wurde weder eine USB-Partition gemountet noch ein Restic-Kommando
ausgeführt. Die Produktivfreigabe bleibt bis zum nachweislich getrennten
Test-Restore und zur Prüfung der exakten 1.0.0-Dateien gesperrt.

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
