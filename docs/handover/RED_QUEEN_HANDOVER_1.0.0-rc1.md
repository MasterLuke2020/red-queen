# RED QUEEN — HANDOVER 1.0.0-rc1

## 1. Aktueller Source-of-Truth-Stand

- Produktname: **Red Queen**
- Version: **1.0.0-rc1**
- Status: **LIVE VERIFIED**
- Release Channel: `release_candidate`
- Release Phase: `rc`
- Candidate: `rc1`
- RC Blocker: **0**
- Historischer Entwicklungsname: WNHF
- Verifizierte Entwicklungsbasis: WNHF `1.27.0` / `WP-4.7.9.1`
- Technische HA-Domain bleibt: `wnhf`
- Services bleiben: `wnhf.*`
- Config/Persistence bleibt: `/config/wnhf`
- RC1 ZIP SHA-256: `c59388733a488cb9df075e02a5d6bff36398147bb29d6a57465bc495af0ee365`

## 2. Architektur

Kanonischer Pfad:

```text
House Registry / HA Feedback
        ↓
House Model / State
        ↓
Context + Rules + Policies + Decisions
        ↓
Capabilities
        ↓
Providers
        ↓
Canonical Execution
        ↓
Feedback Guard / Effect Confirmation
        ↓
Qualification + Diagnostics
```

Grundprinzip: Red Queen ist eine zentrale semantische Intelligenz über der Hausautomation. Manuelle Bedienung darf durch Context/Rules/Policies/Decisions nicht grundsätzlich blockiert werden; reale Automationsausführung erfolgt nur über explizite Verträge und Provider/Feedback-Prüfungen.

## 3. Aktueller 1.0-RC-Scope

Aktiv: rooms, lighting, openings, covers, security, providers, capabilities, qualification, validation, rules, context, policies, decisions, execution, scheduler.

Geplant/nicht im stabilen RC1-Scope: climate/temperature, media, notifications, aktive garage/gate execution.

Covers sind **teilweise fertig**: Registry, semantischer Zustand, Native Cover Surface und `covers.snapshot` sind vorhanden; kanonische mutierende Cover-Actions sind noch nicht Teil des stabilen Execution Surface.

## 4. Canonical Execution

Neue produktive Automationen verwenden:

```text
wnhf.execution_execute
```

Dry Run:

```text
wnhf.execution_dry_run
```

- Canonical API: `1.0`
- Execution Contract: `1.2-stage4.7.4`
- RC1 real-execution-enabled Action: `lighting.turn_off`
- Target: exakt ein `object_id`
- Parameter: keine
- Strategie am verifizierten Licht: `guarded_momentary_pulse`

Readiness ist sauber getrennt:

- declared
- semantically_ready
- real_execution_enabled
- executable_now

Live verifiziert: 5 declared, 5 semantically ready, 1 real-execution-enabled, 1 executable-now.

## 5. Verifizierte Hardware-Pfade

### Idempotency

Feedback bereits OFF → **kein Command** → `EXE-101 already_satisfied`.

Persistente Evidenz bei RC1-Freigabe: 7 Passes.

### Real Success

Feedback ON → genau ein Command → Feedback OFF bestätigt → `EXE-000 succeeded`.

Letzte verifizierte reale Execution:

- Execution ID: `exe_20260809T161726_999223Z_0733606f`
- Action: `lighting.turn_off`
- Object: `light.eg.kitchen.spots`
- Command: `button.btwebeglichtkuechespots`
- Feedback: `binary_sensor.qxeglichtkuechespots`
- Result: `EXE-000`
- command_sent: true
- feedback_confirmed: true

Persistente Real-Success-Evidenz bei RC1-Freigabe: 4 Passes.

Gesamt: **11 persistierte Passes**, 1 hardware- und framework-verifizierte Action.

## 6. Qualification

Store:

```text
/config/wnhf/qualification/execution_evidence_store.json
```

- automatic_collection_enabled: true
- persistence_enabled: true
- store loaded: true
- load_error: null
- write_error: null
- Qualification ist **keine Execution-Autorisierung**.

Config-Entry Reload wurde verifiziert: volatile last-execution-Daten werden zurückgesetzt, persistente Evidence bleibt erhalten.

## 7. Public API

66 Services, exakt einmal klassifiziert:

- Stable Public: 8
- Diagnostic Public: 34
- Maintenance Public: 4
- Legacy/Development: 20
- duplicates: 0
- complete: true

Stable Public:

- `wnhf.execution_execute`
- `wnhf.execution_dry_run`
- `wnhf.system_status`
- `wnhf.release_scope`
- `wnhf.release_info`
- `wnhf.public_api`
- `wnhf.qualification`
- `wnhf.upgrade_check`

`wnhf.execute` ist Legacy Decision-ID Execution und nicht für neue Automationen empfohlen.

## 8. Finaler Live-Status der Referenzinstallation

- House: Weidnerhome
- Rooms: 22
- Lights: 43
- Enabled Lights: 40
- Controllable Lights: 38
- Covers: 17
- Openings: 21
- Decisions: 5
- Policies: 5
- Registry valid: true
- Validation quality: 100
- Runtime health: 100
- Errors: 0
- Warnings: 0

## 9. RC1 Smoke Test nach Branding/Packaging

Auf dem tatsächlichen `Red_Queen_1.0.0-rc1.zip` live bestanden:

- Startup PASS
- `wnhf.release_info` PASS
- `wnhf.system_status` PASS, Health 100
- `wnhf.public_api` PASS, 66/66
- `wnhf.qualification` PASS, Evidence 11 unverändert

Keine zusätzliche Hardware-Execution nach dem Branding war nötig, da die Execution-/Provider-/Feedback-/Qualification-Logik aus der bereits verifizierten Basis unverändert übernommen wurde.

## 10. Bekannte Grenzen / nächster Entwicklungsschritt

RC1 ist im Feature Freeze. Kein Nachschieben von Temperatur, Cover-Control, Garage, Media oder Notifications in `1.0.0-rc1`.

Wenn ein echter RC-Fehler auftritt: Fix → neue Candidate-Version, z. B. `1.0.0-rc2`, danach Regression Gate.

Wenn RC1 stabil bleibt: nächster Release-Schritt → **Red Queen 1.0.0 Final**.

Erst danach neue Feature-Releases. Wahrscheinliche Kandidaten: Temperature/Climate Semantics, canonical Cover Execution, Garage/Gate, Notifications, Media.

## 11. Arbeitsweise im Projekt

Für Home-Assistant-/Red-Queen-Anleitungen bevorzugte Struktur:

1. Architektur / Erklärung
2. Entscheidung
3. Arbeitsauftrag

Nur unter **Arbeitsauftrag** stehen konkrete Schritte in Home Assistant. Tests/Actions als vollständige copy-paste-fähige YAML-Blöcke inklusive `action:` und `data:`.

HA-UI ist Englisch; UI-Bezeichnungen entsprechend auf Englisch nennen.

## 12. Wichtige externe Abgrenzungen

- Generische Home-Assistant-Warnung „custom integration ... has not been tested“ ist bei lokaler Custom Integration erwartet.
- `siemens_ozw672` Duplicate-Unique-ID-Fehler gehören nicht zu Red Queen.
- Ein während RC-Tests beobachteter instabiler Licht-Feedbackstatus wurde bei deaktiviertem Red Queen reproduziert und als externes `asyncua`-Thema geklärt; er war keine Red-Queen-Regression.

## 13. Name

**Red Queen** ist ab RC1 der öffentliche Framework-Name. WNHF bleibt nur als historische Entwicklungslinie und technischer Home-Assistant-Identifier bestehen. Das Branding soll eigenständig sein; keine offiziellen Film-/Franchise-Logos oder Figurenbezüge.
