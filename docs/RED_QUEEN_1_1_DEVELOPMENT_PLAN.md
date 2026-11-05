# Red Queen 1.1.0 – Smart Living Edition
## Technisches Pflichtenheft und gebündelter Entwicklungsplan

**Status:** Entwicklungsplanung – kein freigegebener Release
**Ausgangsbasis:** Red Queen 1.0.0, GitHub main, Commit 66d51ba90ca608bf94eb3f6740200379c040e450
**Entwicklungszweig:** feature/1.1.0-smart-living
**Grundsatz:** Bestehende Produktion und main bleiben bis zur nachgewiesenen Freigabe unverändert.

## 1. Ziel und Abgrenzung

Ein integriertes 1.1.0-Release aus (A) Betriebsmodi/Hausregeln, (B) RGBW/Dimmen/Szenen und (C) Durchsagen/Benachrichtigungen/Dashboard. Die Funktionen werden zusammenhängend im Entwicklungsbranch implementiert, automatisch geprüft und erst danach in einem einzigen gebündelten Home-Assistant-Staging-Lauftest qualifiziert.

Nicht Bestandteil: allgemeiner grafischer Regel-Designer, Heizungs-/PV-Optimierung, vollwertige neue Media-Player-Plattform, vollständiger Presence-Tracker, automatische Änderungen am SPS-Programm, unkontrollierte Zugangsschaltungen.

## 2. Verifizierter Stand von 1.0.0

| Bereich | Vorhandene Basis | Zu entwickelnde Erweiterung |
| --- | --- | --- |
| HouseSnapshot/HouseState | Technische Zustände ready/activity/attention/error | Eigenständige Betriebsmodi, unabhängig vom Gesundheitszustand |
| RuleEvaluator und YAML-Loader | Deklarative Bedingungen, priorisierte Kontextregeln | Hausmodus-Fakten und erklärbare Moduswahl |
| PolicyEvaluator | off/monitor/enforce, allow/deny | Schutz ausgewählter kanonischer Aktionen unter definierten Betriebsmodi |
| Light-Domain/Native Light | monitor_only/toggle/reserved, ONOFF | RGBW-/Brightness-Datenmodell, Adapter und Farbfeedback |
| Canonical Execution | Validierung, Provider-Routing, Guard und Audit | Explizite neue Aktionsverträge, keine direkten Hardware-Bypässe |
| NotificationCapabilityProvider | send, announce, route; Sonos-Overlay | Einfache Oberfläche, Quiet-Hours, Prioritäten, Deduplizierung |
| Managed Configurator / Dashboard | Transaktionssicheres Registry-Editing, generiertes Dashboard | Neue Entitätstypen und schnelle Bedienkarten |

**Gefundener Integrationspunkt:** Die Beispielkonfiguration der Benachrichtigungen referenziert sensor.wnhf_house_state. Die native House-Status-Entität im aktuellen Quellcode verwendet jedoch die vorgeschlagene ID sensor.wnhf_house_status und liefert nur ready/activity/attention/error. Für home/away/vacation wird daher eine **eigene** House-Mode-Entität benötigt; die Beispiel-Route wird mit der tatsächlichen Installation abgeglichen.

**Achtung:** Die alte Repository-Verifikation ist auf den unveränderlichen 1.0.0-Release und dessen Source-Checksums festgelegt. Für 1.1.0 muss eine **separate versionierte Release-Qualifikation** entstehen, bevor Source/Manifest/Checksum offiziell umgestellt werden. Der 1.0.0-Nachweis wird nicht rückwirkend umgeschrieben.

## 3. Paket A – House Intelligence

### 3.1 Datenmodell

Zwei unabhängige Achsen:

1. **Technische Hausgesundheit:** bestehende ready/activity/attention/error; keine Umdeutung.
2. **Betriebsmodus:** home, away, vacation; mit unabhängigen Overlays sleeping und guests.

Die Modusquelle und deren Erklärung sind Bestandteil des Snapshots: manual, verified_presence, schedule, default; zusätzlich timestamp, priority, override_expiry und reason.

Die erste Version arbeitet ohne behauptete automatische Personenerkennung. Moduswechsel sind manuell möglich; automatische Präsenzregeln nur bei **explizit konfigurierten, verlässlichen** HA-Entitäten. Unbekannte Signale dürfen keinen selbsttätigen Wechsel auf away/vacation auslösen. Vacation bleibt anfangs manuell zu aktivieren.

### 3.2 Priorität und Regelwirkung

1. Unveränderliche Ausführungs-/Sicherheitsguards haben Vorrang.
2. Explizite Betriebsmodus-Policies sind für neue Automatikaktionen bindend.
3. Zeitlich begrenzte manuelle Overrides betreffen nur Komfortfunktionen.
4. Verifizierte Präsenz-/Zeitregeln ermitteln den normalen Modus.
5. Im Zweifelsfall kein unbeaufsichtigter Aktorwechsel; Zustand erklären.

Policies werden zunächst in monitor geprüft, danach für explizit konfigurierte Aktionen kontrolliert auf enforce umgestellt. **Bestehende Besonderheit:** nicht konfigurierte/abgeschaltete Policies liefern aktuell allow. Deshalb darf die neue Automatik für sicherheitsrelevante Aktionen nicht von einer impliziten Policy ausgehen; eine fehlende erforderliche Policy wird vor Ausführung explizit abgefangen.

Die Policy-Durchsetzung gilt für Befehle, die den kanonischen Red-Queen-Ausführungspfad nutzen. Ein manueller WAGO-Schalter oder direkter Home-Assistant-Dienst außerhalb dieses Pfads wird dadurch **nicht** gesperrt. Grundbeleuchtung muss bei Red-Queen-Ausfall lokal bedienbar bleiben. Keine automatischen Garagen-, Türöffnungs- oder Entriegelungsaktionen in 1.1.

### 3.3 Bedienung

HA-Entität für Betriebsmodus, Status/Fakten/Sperrgründe und manuelle Overrides. Konfiguration im Managed Configurator mit Rückwärtskompatibilität. Schon vorhandene IDs und YAML-Strukturen bleiben gültig.

## 4. Paket B – Smart Lighting

### 4.1 Steuerflächen

Native HA-Lichtentität unterstützt, sofern die zugrunde liegende Hardware dazu qualifiziert ist:

- ON/OFF und Helligkeit
- RGBW-Farbwerte einschließlich **separatem Weißkanal**
- konfigurierbare sanfte Übergänge (nur falls Provider unterstützt)
- aktuelle Farbe/Helligkeit und reale Verfügbarkeit
- Haus-/Raumgruppen sowie gespeicherte Lichtstimmungen

Bestehende Impuls-Taster-Lichter verbleiben vollständig kompatibel auf ONOFF. Keine Umstellung alter Einträge ohne ausdrückliche Konfiguration.

### 4.2 Adapterstrategie

- **HA-Light-Adapter** für bereits als light.* mit passendem supported_color_modes exponierte Lampen.
- **WAGO/OPC-UA-Adapter** für die tatsächliche DALI-/Kanalsteuerung. Benötigt dokumentierte schreibbare Variablen, Wertebereiche, Trigger/Commit-Semantik und lesbare Rückmeldungen. Die endgültige Adapterform folgt erst aus der Produktionsinventur und ggf. dem SPS-Projekt; keine geratenen NodeIDs.

Ergänzung der kanonischen Ausführungsverträge für Brightness/RGBW/Scene, Provider-Validierung und Ergebnis-Audit. Fehlende Rückmeldung darf nicht als bestätigter Erfolg dargestellt werden. Bei kanalweise geschriebenem RGBW wird kein atomarer Farbwechsel behauptet.

### 4.3 Szenen und Gruppen

Szenen sind deklarative Sollwerte pro Raum oder Gruppe, zunächst manuell oder durch bestätigte Komfortregeln ausgelöst. Idempotenz, Per-Target-Status und manuelle Übersteuerung verhindern automatische Gegenbefehle unmittelbar nach Benutzerinteraktion.

## 5. Paket C – Notifications & Announcements

Vorhandene kanonische Aktionen notifications.send, notifications.announce und notifications.route sowie der Sonos-Ankündigungs-Overlay-Pfad werden **wiederverwendet**. Keine parallele neue Sonos-Snapshot-/Restore-Logik.

Erweiterungen:

- konfigurierbare Empfänger, Räume, Lautsprecher und Audio-Level
- Informations-, Hinweis-, Warn- und Alarmklassen
- Ruhezeit-/Schlafmodus-Routing; kritische Push-Meldungen bleiben bei Bedarf möglich
- begrenztes Rate-Limit/Deduplizierung pro Nachrichtenquelle und Ereignisschlüssel
- nachvollziehbares Dispatch-Audit mit korrekter Semantik: Dienstannahme ist kein Beweis, dass das Smartphone die Meldung anzeigt oder die Ansage gehört wurde
- UI für manuelle Tests und Schalten von Profilen ohne rohe EntityIDs

Sicherheitsrelevante Sprachwarnungen dürfen nur nach expliziter Konfiguration Quiet-Hours-Ausnahmen nutzen.

## 6. Dashboard / Performance

Integration in das bestehende generierte Red-Queen-Dashboard, mit eigener Smart-Living-Ansicht und Raumkarten für RGBW. Keine zusätzlichen permanenten Vollhaus-Polling-Schleifen, keine massiven JavaScript-Karten auf alten Tablets. Dashboard-Schreibvorgänge behalten den bisherigen bewusst bestätigten Create/Update-Mechanismus; fremde Dashboards werden nicht überschrieben.

## 7. Versions- und Migrationsvertrag

- Technische Domain bleibt wnhf.
- Bestehende Objekt- und Entity-Unique-IDs bleiben stabil.
- Manuelle Registry wird nicht automatisch übernommen.
- Managed-Änderungen erhalten Vorvalidierung, Backup und Rollback.
- Fehlende optionale 1.1-Konfiguration ergibt einen gültigen, funktionierenden 1.0-ähnlichen Betrieb.
- Konfigurationsmigration erfolgt kontrolliert, idempotent und mit Rückfallpfad; keine stillen gefährlichen Default-Aktionen.
- Kompatibilität von 1.0-Dashboard, lokalen Schaltern und existierenden Sonos-Routen wird geprüft.

## 8. Arbeitspakete und Abnahmegates

| Block | Umsetzung | Automatische Gate-Tests |
| --- | --- | --- |
| 0 – Inventur | tools/rq11_inventory.py und Mapping-Bericht | Lesen ohne Mutationen, sensible Dateien ausgeschlossen |
| A – House | Betriebsmodi, Fact-Bridge, Policies, Status-Entität | Prioritäten, unknown, Override, missing-policy, legacy state |
| B – RGBW | Registry, Lichtplattform, Adapter, Ausführungsvertrag, Szenen | Wertebereiche, Farb-/Weißkanal, fehlendes Feedback, alte Taster |
| C – Kommunikation | bestehender Provider + UI, Ruhezeit, Deduplizierung | Priority-Route, DND, Wiederholung, Announce-Nichtunterbrechung |
| D – UI/Release | Dashboard, Migration, Dokumentation, Release-Paket | Render-Digest, alte IDs, Konfigurator, Install/Restart/Rollback |

**Ein manueller Staging-Durchlauf** nach bestandenen automatischen Checks: bestehende ONOFF-/Raffstore-/Garagenfunktionen, ein RGBW-Objekt mit echtem Feedback, eine Sonos-Durchsage während Musik, eine Push-Meldung, House-Mode-Policy, Dashboard-Performance und HA-Restart. Bei Regression keine Produktionsfreigabe.

## 9. Nächste konkrete Schritte

1. Produktionsinventur mit dem read-only Collector durchführen; Ergebnis bleibt zunächst lokal und wird vor Weitergabe geprüft.
2. RGBW-Ausführungsweg aus realen OPC-UA-/DALI-Entitäten und bei Bedarf dem SPS-Programm bestimmen.
3. Pakete A/B/C in zusammenhängenden GitHub-Änderungen implementieren, automatisierte Tests ergänzen und per Draft-PR sammeln.
4. Staging-Qualifikation und erst anschließend 1.1.0-Stable-Release.

**Nicht aus dem GitHub-Quellcode ableitbar:** Tatsächlicher SPS-DALI-Aufbau, OPC-UA-Schreibbereiche, Laufzeitfähigkeiten der HA-Lichter, reale Präsenzsensoren und aktive Produktionsregeln. Der Collector dokumentiert bekannte Zuordnungen, aber keine Live-Zustände oder SPS-Quelle.
