# Red Queen 1.2 – Herstellerunabhängige Lichtsteuerung

**Status:** Entwicklung, nicht produktiv freigegeben. Kein Zugriff auf echte
Leuchten oder Hardware während der automatisierten Tests.

## Grundprinzip

Red Queen steuert Lichtquellen über ihre **Home Assistant light.*-Entität**
und deren tatsächliche \`supported_color_modes\`, statt über Hersteller oder
Integrationsnamen. Das gilt z. B. für Shelly, DALI/OPC UA, MQTT/Zigbee,
WLED oder andere direkte HA-Lichtintegrationen. Keine direkten Shelly-APIs,
keine hardcodierten Herstellerbefehle.

| HA unterstützte Farbmodi | Red Queen Szenenfelder |
| --- | --- |
| onoff | EIN/AUS |
| brightness | EIN/AUS + Helligkeit |
| rgb, hs oder xy | Helligkeit + RGB |
| rgbw oder rgbww | Helligkeit + RGB und RGBW-Kanäle |
| color_temp | Helligkeit; separate Farbtemperatur-UI ist nicht Teil dieses Schritts |

Der aktive aktuelle Farbmodus ist **nicht** die Grundlage: relevant sind
\`supported_color_modes\` aus dem HA-Zustand. Fehlt diese Information oder
ist die Leuchte unavailable/unknown, wird sie nicht als *neue*
Auswahl angeboten. Bei späteren Änderungen bleiben bisherige Szenen
gespeichert; ihre fehlerhaften Quellen werden beim Dispatch blockiert.

**Shelly-Einschränkung:** Ein Shelly RGBW-Controller muss tatsächlich
als \`light.*\` mit RGBW-Fähigkeiten verfügbar sein. Ein bloßer Shelly
Relais-/Schaltaktor bietet nur EIN/AUS. Red Queen verwandelt einen
Schaltaktor nicht durch Software in einen RGBW-Controller.

## GUI-Ablauf

\`Red Queen → Konfigurieren → Smart Lighting → Szenen\`

1. Neue Szene anlegen oder eine bestehende öffnen.
2. **Licht auswählen**: Liste zeigt direkte, aktive HA-Leuchten aller
   Hersteller. Die Benutzerwahl ist eine explizite Berechtigung für
   genau diese Szenenquelle, **keine Haus-weite Freigabe**.
3. Erst danach zeigt das Szenenformular die von dieser Entität
   unterstützten Eigenschaften (EIN/AUS, Helligkeit, RGB, RGBW).
4. Speichern aktualisiert nur den Editor Store, nicht die Hardware.
   Bei HA-Integrationsreload werden die in Szenen ausgewählten externen
   Lichtquellen erneut anhand des Registrys und des Zustands freigegeben.

Bestehende YAML-Einstellungen \`rgbw_entity_ids\` und \`discover_dali\`
funktionieren als Legacy-Kompatibilität weiter. Die automatische
DALI-Erkennung bleibt nur für alte Installationen erhalten; **neue
nicht-DALI-Leuchten können direkt im Editor ausgewählt werden** und
brauchen keinen eigenen Herstelleradapter.

## Sicherheitsgrenzen

- Niemals die ganze Liste von HA-Leuchten automatisch schalten.
- GUI-ausgewählte externe Leuchten gehören zu
  \`scene_external_targets\` und werden **nicht** in die ältere
  \`rgbw_targets\`-Liste für das globale RGBW-Alles-AUS übernommen.
- Eigene Red-Queen-Entitäten und bekannte HA-Proxy-/Gruppenplattformen
  \`template\`, \`group\` werden als externe Quellkandidaten ausgeschlossen
  (Schutz vor unkontrollierten Rekursionen oder Fanout).
- Auch nach Speicherung gelten der bisherige Szenen-Allowlist-Check,
  Echtzeit-Zustandsprüfung, HA-Farbmodi-Validierung und separate
  Schutzregeln für kanonische Red-Queen/WAGO EIN/AUS-Leuchten.
- Ein erfolgreicher HA-Serviceaufruf beweist **nicht** die physische
  Farb- oder Zustandsrückmeldung.
- Für RGBWW-Leuchten erlaubt der Editor auch RGBW-Parameter, deren
  interne Farbkonvertierung HA/der Herstellerintegration obliegt.
  Eine dedizierte RGBWW- oder Farbtemperatur-Oberfläche wäre ein
  eigener Entwicklungsschritt.

## Testabdeckung

- \`tests/test_rq12_vendor_neutral_light_sources.py\`:
  RGBW Shelly, DALI, MQTT/Zigbee, WLED, einfache Shelly-Relais sowie
  Ausschluss fremder/missing/proxy/unavailable Entitäten.
- \`tools/rq12_ci_editor_flow.py\`: echter HA-OptionsFlow, zweistufige
  Lichtauswahl und capability-spezifische Felder, einschließlich
  Shelly RGBW und ONOFF.
- \`tools/rq12_ci_semantic_lights.py\`: wirklicher HA-Runtime-Import,
  bewusst synthetische Shelly-Entität, native HA
  \`light.turn_on\`-Serviceaufrufe mit RGBW und Helligkeit.
  Kein privates Gerät, Netzwerk oder Hersteller-SDK.

**Release-Gate:** Reale Shelly-Hardware wurde nicht getestet. Für die
Freigabe von 1.2 müssen wir eine Shelly-RGBW-Leuchte in einer isolierten
Staging-Umgebung bzw. an einem Teststand mit Istzustand und Farben prüfen.
Die Außenbeleuchtung im produktiven Haus bleibt bis zur bestätigten
Übergabe unter den bestehenden zwei HA-Automationen.
