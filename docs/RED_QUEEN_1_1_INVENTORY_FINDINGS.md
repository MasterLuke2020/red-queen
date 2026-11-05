# Smart Living 1.1 – Entwicklungsintegration (nicht produktiv freigegeben)

## Auswertung der realen Inventur vom 2026-11-05

- Home Assistant 2026.9.2 / Red Queen 1.0.0
- 2.276 HA-Entitätsregistrierungen; 361 `asyncua`-Entitäten
- 23 Räume, 43 semantische Red-Queen-Lichter (34 aktiv steuerbare Toggle-Leuchten), 17 Covers, 21 Openings, 13 Pflanzen
- 13 **aktive** `light.dali_*_rgbw`-Entitäten aus `asyncua` für Erd-/Obergeschoss
- 1 DALI-Templateauswahl und 1 vorhandene HA-Lichtgruppe; diese werden **nicht** als RGBW-Ziel dupliziert
- 5 Sonos-`media_player`-Entitäten, 2 aktive Announcement-Routen (Büro + Haus), 1 eingerichtetes mobiles Benachrichtigungsziel
- `binary_sensor.datawebstateabwesenheit` / `binary_sensor.datawebstatenight` / `binary_sensor.wnhf_quiet_mode_active`
- `notification.route.house` referenziert `sensor.wnhf_house_state`; dieser Entity-ID-Eintrag fehlt im statischen Inventar. Red Queen 1.0 besitzt nur den technischen Hausstatus. 1.1 kann bei fehlendem/unbekanntem alten Referenzsensor auf seinen **separaten** Betriebsmodus zurückgreifen.
- Keine eigenen Kontextregeln in `contexts/rules`; vorhandene Policies/Decisions beziehen sich derzeit auf Licht-Ausschaltaktionen
- Keine Inventurwarnungen

**Zusätzliche Abnahme:** Isolierter HA-Staging-Start und Registrierung von 5 neuen Hausmodus-/Nachrichtenentitäten erfolgreich (`PASS`). Danach wurden alle 13 produktiven DALI-Quellleuchten in HA mit `supported_color_modes=[ColorMode.RGBW]` gelesen. Der Anlagenbetreiber hat ausdrücklich bestätigt, dass sämtliche 13 RGBW-Leuchten bereits real auf Farbe und Helligkeit getestet wurden und direkt verwendet werden sollen. Es gibt daher keine erneuten Einzel-Hardwaretests als Voraussetzung.

## Umgesetzter Funktionskern im Entwicklungsbranch

### A. Hausmodi

- Eigener `select.wnhf_house_mode` (HA-Rename möglich, stabile Unique-ID `wnhf_smart_living_house_mode`)
- Manuelle Modi `home`, `away`, `vacation` bleiben nach HA-Neustart über HA Store erhalten
- Optionaler automatischer Away-Sensor nur bei explizitem `auto_away: true`; in dieser Installation ist das Signal bekannt, aber die Interpretation noch nicht live geprüft. Daher standardmäßig **aus**.
- Ruhemodus nutzt den vorhandenen `binary_sensor.wnhf_quiet_mode_active`
- `wnhf.house_mode_snapshot` und `wnhf.house_mode_set` als HA-Dienste
- Pure Komfort-Permission-Engine für automatische Lichtszene und Durchsagen. Manuelle Lichtbedienung bleibt erlaubt. **Bestehende kanonische Zugangswächter bleiben maßgeblich.**

### B. DALI / RGBW

- Die bereits vorhandenen, real getesteten `asyncua`-Entitäten `light.dali_*_rgbw` werden **direkt und ohne zusätzliche Home-Assistant-RGBW-Proxy-Entitäten** im Smart-Living-Dashboard eingebunden. Die Laufzeit-Discovery erlaubt nur aktivierte registrierte Quellleuchten, alternativ explizites Allowlisting in `/config/wnhf/smart_living.yaml`.
- Quelle und physisches Treiberverhalten bleiben bei HA/OPC-UA. Direkte Dashboard-Bedienung nutzt den vorhandenen HA-Lichtservice. Optionale Red-Queen-Szenen delegieren validierte RGBW-/Helligkeitsbefehle an denselben HA-Lichtservice. Es gibt noch keinen neuen kanonischen `lighting.set_rgbw`-Ausführungsvertrag.
- Es werden bewusst **keine** neuen `wnhf_rgbw_*`-Unique-IDs und keine doppelten Licht-Entitäten erzeugt. Alle bestehenden Licht- und Toggle-Entity-IDs bleiben unverändert.
- `rgbw_dispatch_audit` dokumentiert nur die über Red Queen ausgelösten Szenen-/Service-Weiterleitungen, nicht direkte Bedienung der Quellleuchte aus Home Assistant und keine physisch bestätigten Farben.
- Die 13 Quellleuchten melden alle `ColorMode.RGBW` und sind nach Betreiberangabe physisch getestet. Die Smart-Living-Kacheln zeigen die nativen HA-Farb-/Helligkeitsfunktionen der vorhandenen Quellleuchten.
- Optionale konfigurierte Lichtszenen können mehrere geprüfte Leuchten nacheinander stellen, werden aber niemals automatisch beim Laden aktiviert; partial dispatch wird sichtbar. Referenzkonfiguration: `configuration/smart_living.example.yaml`.

### C. Kommunikation

- Bestehende `notifications.route` wird verwendet; keine neue parallele Sonos-TTS-Implementierung.
- Native `text`/2×`select`/`button`-Entitäten für die Nachrichteneingabe, Kanal (`mobile`, `voice`, `broadcast`), Priorität (`info`, `warning`, `critical`) und Versand.
- Neue manuelle UI-Durchsagen werden bei `away`, `vacation` und aktivem Ruhemodus unterbunden. Mobile Nachrichten bleiben möglich.
- Doppeleingaben desselben Textes innerhalb von 10 Sekunden werden abgewiesen. Andere externe Meldungserzeuger sind davon bisher **nicht** erfasst.
- Der Text bleibt im Composer während der laufenden HA-Sitzung; Home-Assistant-Recorder/History können Entitätszustände dennoch speichern. Für vertrauliche Inhalte muss die `text`-Entität im Recorder ausgeschlossen werden.
- Die bisherige Notification-Konfiguration bleibt unverändert; nur die Interpretation einer fehlenden alten Modus-Referenz verwendet den neuen Laufzeitmodus.

## Optionale Installationseinstellungen (noch nicht in Produktion verwenden)

Optional `/config/wnhf/smart_living.yaml`:

```yaml
auto_away: false
away_entity_id: binary_sensor.datawebstateabwesenheit
quiet_entity_id: binary_sensor.wnhf_quiet_mode_active
discover_dali: true
rgbw_entity_ids: []
message_route_id: notification.route.house
scenes: []
```

Fehlt die Datei, werden diese konservativen Defaults verwendet. `discover_dali` ist nur Entitäts-Discovery, kein eigenständiger Schaltvorgang. Es werden **keine** Haus-/Urlaubsaktionen automatisch ausgeführt.

## Abnahmehindernisse vor stable 1.1.0

1. **HA-Staging-Test:** alle neuen nativen Plattformen und Konfigurator-Neustart gegen die konkrete HA-Version laden; MQTT/OPC-UA-Hardware bleibt zunächst unangetastet.
2. **Farbmodus-Messung:** einen repräsentativen DALI-HA-RGBW-Kanal samt Weiß- und Helligkeitsfeedback kontrolliert prüfen.
3. **Ausführungsarchitektur:** RGBW-Adapter in die kanonischen Capabilities/Execution-Contracts integrieren oder ausdrücklich einen formal freigegebenen, gleichwertigen Guarded-Adaptervertrag einführen.
4. **House policies:** bestehende Aktionspfade `execution_execute` nicht stillschweigend auf neues Mode-Enforce umstellen; erforderliche Policy-Fall-Closed-Tests ergänzen.
5. **Durchsagen:** Router-Broadcast-Overrides und andere externe Aufrufer zusätzlich auf Hausmodus/Quiet-Hours-Policy prüfen; keine stillen Ruhemodus-Umgehungen.
6. **Szenen/Gruppen:** gegen neue native Red-Queen-Entitäten definieren; noch nicht umgesetzt.
7. **Release-Prozess:** 1.1.0-Versionen, Checksumkatalog, Kompatibilitäts-/Migrationstests, HACS-Staging und Rollback durchführen.
8. Der alte 1.0.0 Source-Checksum-Validator bleibt unverändert; ein separater Entwicklungsvalidator ersetzt *nicht* die Release-Qualifikation.

**Produktionsfreigabe: NO-GO.** Der Entwicklungsbranch ist ausdrücklich nicht als stabile Installation bestimmt.
