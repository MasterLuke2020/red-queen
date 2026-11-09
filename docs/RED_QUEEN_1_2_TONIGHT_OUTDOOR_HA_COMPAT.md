# Red Queen 1.2 — sichere Übergangslösung für den Abend

**Status:** Manuell einzurichtende HA-Automationen, standardmäßig deaktiviert.
**Kompatibilität:** Produktive Red Queen **1.1.0**. Kein Domain-Wechsel,
kein HACS-Upgrade, keine WAGO-Änderung nötig.

## Warum diese Zwischenlösung?

Die Domain-Migration auf `red_queen` und die 1.2-Automatisierung sind
noch **nicht** mit der tatsächlichen Haus-Konfiguration und Hardware
abgenommen. Vor einem garantierten Abendbetrieb ist die isolierte
Home-Assistant-Automatik sicherer und kurzfristiger testbar.

## Exakter Umfang

Nur:
1. `light.wnhf_garage_aussen_up_down`
2. `light.hof_vorplatz_red_queen_strasse_up_down` (noch **ungeprüft**)
3. `light.wnhf_hof_up_down`

Im aktuellen Registry-Inventar gibt es einen weiteren Straßenkandidaten:
`light.wnhf_strasse_up_down`. **Vor dem Aktivieren** beide Straßen-
Entitäten über Home Assistant einzeln physisch testen und genau eine
korrekte Entität in **beiden** YAML-Automationen verwenden.
Alle anderen Außen- und Innenlichtkreise bleiben ausgeschlossen.

## Einrichtung (HA UI)

1. Über **Entwicklerwerkzeuge → Zustände** die exakten Entitäts-IDs
   prüfen. Garage und Hof einzeln über die reguläre HA-Lichtsteuerung
   physisch auf EIN/AUS testen. Die beiden Straßenkandidaten einzeln
   testen; anschließend die physisch richtige ID in den Vorlagen wählen.
   Nicht weiterarbeiten, wenn ein Kreis bereits direkt über WAGO oder
   Home Assistant nicht korrekt reagiert.
2. **Einstellungen → Automatisierungen & Szenen → Automatisierung erstellen
   → Neue Automatisierung → ⋮ → In YAML bearbeiten.** Den vollständigen
   Inhalt von `ha_native_outdoor_sunset.ui.yaml` einsetzen und speichern.
3. Ebenso `ha_native_outdoor_2300.ui.yaml` als zweite Automatisierung
   speichern. **Beide sind durch `initial_state: false` deaktiviert.**
4. Vor der Aktivierung: Auslösen per *Aktionen ausführen* oder die
   Lichtfunktionen einzeln testen. Dabei das physische Resultat und die
   Statusrückmeldungen prüfen. Niemals den ganzen Bereich schalten.
5. Wenn alles eindeutig stimmt: bei **beiden** Automationen
   `initial_state: false` entfernen, erneut speichern und beide
   Automationen über die UI **aktivieren**. Sicherstellen, dass keine
   zweite Außenlicht-Automation mit denselben drei Kreisen aktiv ist.
6. Am Abend: Sunset-Automation auslösen lassen; drei physische Licht-
   rückmeldungen prüfen. Um 23:00 gezielte Ausschaltung und Rückmeldung
   prüfen. Traces helfen bei Fehlersuche.

## Verhalten

- Nur bei **Sonnenuntergang** EIN. Kein automatisches Wiedereinschalten
  nach Neustart. Eine manuelle Abschaltung nach Sunset bleibt bis zum
  nächsten Sunset wirksam.
- 23:00 Uhr **AUS**, nur drei vorab getestete Entitäten.
- Nach HA-Neustart: Nachholung des Nacht-AUS nur, wenn Uhrzeit >= 23:00
  oder vor 12:00 und `sun.sun` auf `below_horizon` steht. Kein
  automatisches ON bei HA-Neustart. Ohne `sun.sun`-Status kein
  nachgeholtes OFF (fail closed).
- Ein gezieltes manuelles EIN nach 23:00 bleibt bis zum nächsten
  Neustart oder regulären AUS unberührt; ein Neustart in der Nacht
  kann es wieder ausschalten. Diese Politik ist vorerst bewusst simpel.

## Abbau

Sobald der native Red-Queen-1.2-Regeleditor mit derselben Außenlichtszene
produktiv freigegeben wird: **beide Übergangsautomationen deaktivieren**,
bevor die neue Red-Queen-Regel aktiviert wird. Doppelte Automatikbefehle
sind sonst möglich.

**Keine Automationen sind durch diesen GitHub-Commit am Hausserver installiert.**
