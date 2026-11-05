# Red Queen 1.1.0 – einmalige Inventur auf weidnerhome-srv2

## Zweck

Dieses Inventurskript ist ein **reiner Lesevorgang**. Es erfasst die bestehende Red-Queen-Registry, die vorhandenen HA-Entitätsnamen und Integrationsplattformen sowie die konfigurierten Benachrichtigungs- und Regel-IDs. Es löst keine HA-Dienste aus, ändert keine Konfiguration und erzeugt keine Datei innerhalb des Home-Assistant-Containers.

Die Daten werden ausschließlich auf dem lokalen Server gespeichert. Vor der Weitergabe bitte prüfen, ob Objekt- und Entitätsbezeichnungen private Informationen enthalten.

## Einmaliger Start (ein zusammenhängender Befehl)

Auf weidnerhome-srv2 im Terminal ausführen (Docker-Container: homeassistant):

~~~bash
umask 077; curl -fsSLo "$HOME/rq11_inventory.py" "https://raw.githubusercontent.com/MasterLuke2020/red-queen/4e57ad3a31b66f8031077062c73bfdbdefae557c/tools/rq11_inventory.py" && sudo docker exec -i homeassistant python3 - < "$HOME/rq11_inventory.py" > "$HOME/redqueen_1_1_inventory.json" && python3 -m json.tool "$HOME/redqueen_1_1_inventory.json" >/dev/null && ls -lh "$HOME/redqueen_1_1_inventory.json"
~~~

Das heruntergeladene Skript ist auf den festen Git-Commit 4e57ad3a31b66f8031077062c73bfdbdefae557c gebunden (nicht auf einen veränderlichen Branch). Bei einem Fehler vor dem Docker-Aufruf wird kein Skript im Container gestartet.

## Erwartete Ausgabe

- Gesammelter Bericht: ~/redqueen_1_1_inventory.json
- Lokale Kopie des Collectors: ~/rq11_inventory.py
- Terminal: nur Größe und Dateiname bei erfolgreichem Abschluss
- Fehler: erscheint auf stderr; keine automatische Übertragung

**Bitte lediglich die JSON-Datei nach kurzer Sichtprüfung im Chat hochladen.** Es werden keine Passwörter oder Tokens benötigt.

## Erfasste Informationen

- Versionen von Home Assistant und Red Queen
- Räume, Red-Queen-Lichter, vorhandene Ein/Aus-Bindings
- Anzahl vorhandener Raffstores, Öffnungen, Pflanzen
- ID-Zuordnung der Push-/Sonos-/TTS-Ziele und Nachrichtenrouten
- Benannte benutzerdefinierte Regel-/Policy-/Decision-Dateien
- Relevante HA-EntityIDs (unter anderem light, media_player, tts, notify, OPC UA) einschließlich Herkunftsplattform und deaktiviertem Status
- Warnungen über fehlende oder fehlerhafte, **nicht sensible** Quellen

Der Entitätskatalog wird bei maximal 750 Einträgen abgeschnitten und kennzeichnet dies. Die vollständigen Domain- und Integrations-Anzahlen bleiben enthalten.

## Ausdrücklich nicht erfasst

- HA-Zugangstokens, API-Schlüssel, Passwörter
- secrets.yaml, configuration.yaml, core.config_entries
- HA-Logs und Geräte-Registry
- Live-Schaltzustände, Bewegungs-/Anwesenheitsdaten, Standortdaten
- OPC-UA-Unique-IDs/NodeIDs und SPS-Projektcode
- Netzwerkverbindungen oder aktive Hardwareabfragen

Damit ist die Inventur sicher und schnell, **aber kein vollständiger Nachweis der RGBW-Lauffähigkeit**. Für die tatsächliche DALI-/SPS-Kanalansteuerung kann später eine separate PLC-Mapping-Information erforderlich sein. Die Einheit arbeitet bewusst ohne Schreibzugriffe oder echte Lichttests.

## Fehlerdiagnose

- "Registry not found under /config": Falscher Container oder Red-Queen-Config an anderem Ort. Abbrechen, keine Pfade erraten.
- "No such container": Namen des HA-Containers mit docker ps prüfen.
- Fehlt PyYAML im HA-Container: Collector bricht ohne Dateischreibzugriffe ab.
- Warnungen im JSON bedeuten nicht automatisch, dass der laufende Home Assistant fehlerhaft ist.

## Nächster Entwicklungsschritt

Nach Auswertung der JSON-Datei werden House-Mode-Fakten, RGBW-DALIschnittstelle und Notification-Routen installationsspezifisch finalisiert und die drei großen Softwarepakete in einem gemeinsamen Entwicklungsbranch implementiert.
