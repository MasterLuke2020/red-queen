# Red Queen 1.1.0 – ein gebündelter, isolierter HA-Integrationstest

## Sicherheitsgrenzen

Dieses Skript startet einen eigenen Home-Assistant-Testcontainer. Es verändert nicht das produktive Home Assistant:

- Produktives Docker-Image wird nur gelesen und wiederverwendet (kein Update).
- Produktionscontainer wird weder neugestartet noch gestoppt.
- Es wird lediglich /config/wnhf/house/registry via Docker-Kopie aus dem produktiven HA-Container gelesen.
- Die Testkonfiguration enthält keine produktiven .storage-Zugangsdaten, Secrets, Automationen, Tokens oder Integrations-Konfigurationsdaten.
- Das Staging läuft ausdrücklich mit Netzwerkmodus none und ohne Portfreigaben, ohne WAGO- oder Sonos-Verbindung und ohne produktives /config-Mount.
- Staging-RAM/CPU sind limitiert; unzureichender verfügbarer Host-RAM oder Speicherplatz führt vor dem Start zum Abbruch.
- Nach dem Test wird der isolierte Container gestoppt und entfernt. Lokale Testdateien sind in einem temporären, zugriffsbeschränkten Ordner gespeichert.

Die Isolation verifiziert die Softwareinitialisierung und Registrierung der neuen Entitäten, aber nicht den Betrieb der realen RGBW-Hardware oder Sonos.

## Ein einziger Befehl auf weidnerhome-srv2

Das Skript kann zuerst unter [tools/rq11_stage_check.sh](../tools/rq11_stage_check.sh) gelesen werden. Im Terminal:

~~~bash
curl -fsSLo "$HOME/rq11_stage_check.sh" "https://raw.githubusercontent.com/MasterLuke2020/red-queen/feature/1.1.0-smart-living/tools/rq11_stage_check.sh" && bash "$HOME/rq11_stage_check.sh"
~~~

Das Skript verlangt git, python3, sudo, einen laufenden Docker-Container homeassistant sowie Zugriff auf GitHub. Es greift nicht auf Home Assistant REST-/WebSocket-Tokens zu.

## Danach

Der kompakte Bericht steht unabhängig vom Erfolg unter ~/redqueen11_staging_report.json.

Diesen Bericht bitte nach Sichtprüfung in den Red-Queen-Chat hochladen. Keinen vollständigen .storage-Ordner und keine Home-Assistant-Logs ungeprüft hochladen.

PASS bedeutet: HA-Staging meldete erfolgreiches Red-Queen-Setup und die erwarteten neuen manuellen Hausmodus-/Nachrichten-Entitäten wurden in der isolierten Entity Registry gefunden. INCOMPLETE ist ein Entwicklungsbefund, kein Grund, Änderungen auf dem produktiven Container auszuprobieren.

Die detaillierten, ausschließlich im Staging entstandenen Dateien und Logs bleiben in dem vom Skript ausgegebenen /tmp/redqueen11-stage.*-Ordner und können bei Bedarf später gemeinsam geprüft und gelöscht werden.

## Nach diesem Test

1. Fehler im GitHub-Branch gebündelt korrigieren.
2. Reale unterstützte Farbmodi (supported_color_modes) an einer einzigen repräsentativen DALI-RGBW-Leuchte prüfen (ohne Berechtigungen zu erraten).
3. Vollständige Guard-/Policy- und Routing-Regression qualifizieren.
4. Eine einzige kontrollierte Endqualifikation mit WAGO/Sonos durchführen, bevor 1.1.0 freigegeben wird.

Der Entwicklungsbranch und Draft PR #2 bleiben ausdrücklich nicht produktionsfreigegeben.
