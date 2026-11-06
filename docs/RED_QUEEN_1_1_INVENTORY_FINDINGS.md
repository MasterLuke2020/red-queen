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
- Optionale konfigurierte Lichtszenen können mehrere geprüfte Leuchten nacheinander stellen, werden aber niemals automatisch beim Laden aktiviert; partial dispatch wird sichtbar. **Alle** Szenenaufrufe, einschließlich `button.press` und `wnhf.smart_scene_activate`, sind nur im bestätigten Modus `home` bei verifiziert inaktivem Ruhemodus erlaubt. Einzelne vorhandene DALI-Leuchten bleiben manuell unabhängig davon steuerbar. Referenzkonfiguration: `configuration/smart_living.example.yaml`.

### C. Kommunikation

- Bestehende `notifications.route` wird verwendet; keine neue parallele Sonos-TTS-Implementierung.
- Native `text`/2×`select`/`button`-Entitäten für die Nachrichteneingabe, Kanal (`mobile`, `voice`, `broadcast`), Priorität (`info`, `warning`, `critical`) und Versand.
- Neue Smart-Living-Durchsagen (`source=smart_living`) werden bei `away`, `vacation` sowie aktivem **oder nicht verifizierbarem** Ruhemodus blockiert – auch beim Profil `broadcast`. Mobile Nachrichten bleiben möglich. Eine zweite Prüfung findet im kanonischen `notifications.route`-Provider statt.
- Doppeleingaben desselben Textes innerhalb von 10 Sekunden werden abgewiesen. Andere externe Meldungserzeuger sind davon bisher **nicht** erfasst.
- Der Text bleibt im Composer während der laufenden HA-Sitzung; Home-Assistant-Recorder/History können Entitätszustände dennoch speichern. Für vertrauliche Inhalte muss die `text`-Entität im Recorder ausgeschlossen werden.
- Bestehende 1.0-Notification-Automationen und deren absichtlicher Legacy-`broadcast`-Override bleiben unverändert (insbesondere Alarmwege). Direkte Legacy-Aufrufe von `notifications.announce` liegen außerhalb der neuen Smart-Living-Komfortsperre. Für eine globale Durchsagen-Sperre wäre eine gesonderte, bewusst freizugebende Migration nötig.

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

## Qualifikationsstand und verbleibende Freigabeschritte

**Bestätigt:** Der Netzwerk-isolierte HA-Starttest (Commit `db37a04`) war
`PASS`; fünf neue Hausmodus-/Nachrichten-Entitäten wurden registriert.
Alle 13 DALI-RGBW-Quellen melden `ColorMode.RGBW` und wurden laut
Anlagenbetreiber bereits physisch getestet.

**Neu umgesetzt:** Keine doppelten HA-RGBW-Proxies; direkte Dashboard-
Bindung an die vorhandenen `asyncua`-Quellen. Separate Smart-Living-
Durchsagen-Sperre in Nachrichten-Composer und Kanonischem Router mit
bewahrter Legacy-Alarmkompatibilität. Sämtliche Batch-Szenen haben eine
nicht über HA-Service oder Button umgehbare Komfortsperre. Bei fehlender
Ruhemodus-Rückmeldung wird für neue Komfortaktionen konservativ gesperrt.
Automatische Unit-, Quellcode-Invarianten- und hassfest-Checks laufen im
Entwicklungsbranch.

**Noch offen:**
1. Isolierten HA-Staging-Smoke **auf dem neuesten Entwicklungscommit**
   nach den Codeänderungen erneut ausführen (früherer PASS ist kein neuer PASS).
2. Kanonische RGBW-Szenenadapter-Architektur final qualifizieren;
   der bestehende HA-Lichtservice ist die bewährte physische Bedienebene.
3. Sichere Text-/Benachrichtigungs-Routentests mit geeigneten Mocks,
   anschließend gezielte Sonos-Testdurchsage nach Freigabe.
4. Konfigurierte Szenen im Staging erst mit passenden Quellen virtuell prüfen.
5. Fertiges 1.1.0-Manifest, Versions-/Checksum-Katalog, HACS-
   Kompatibilität, Backups und Rollback qualifizieren.
6. Nach abgeschlossener Freigabe **einen kontrollierten** Produktiv-Rollout,
   mit anschließendem End-to-End-Praxistest durchführen.

Der unveränderte Stable-1.0.0-Source-Checksum-Validator bleibt gültig;
die Branch-Checks ersetzen ausdrücklich keine Release-Qualifikation.

**Produktionsfreigabe aktuell: NO-GO.** Noch keinen Entwicklungsstand
über die laufende Red Queen 1.0.0 kopieren.
