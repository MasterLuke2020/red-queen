# Red Queen 1.1.0 – RGBW-Fähigkeiten ohne Schaltbefehl prüfen

## Nach dem isolierten HA-Staging

- Red Queen Entwicklungsstand db37a04: isolierter Staging-Start PASS.
- Hausmodus und vier Nachrichten-Bedienelemente in der Staging-Entity-Registry registriert.
- Keine WAGO-/Sonos-/DALI-Verbindung im Staging; Farbmodi müssen aus dem aktiven HA gelesen werden.
- Produktive Red Queen bleibt bei 1.0.0, bis 1.1.0 freigegeben ist.

## Einmalige, rein lesende Abfrage

Produktives Home Assistant → Entwicklerwerkzeuge → Vorlagen (Template).
Folgenden Jinja-Block einfügen und Ergebnis an Red Queen Entwicklungs-Chat übermitteln.
Die Vorlage ruft keinen Service auf und ändert keine Entity.

~~~jinja2
{% set rgbw = [
  'light.dali_eg_bad_wc_rgbw',
  'light.dali_eg_buro_rgbw',
  'light.dali_eg_gang_rgbw',
  'light.dali_eg_kuche_rgbw',
  'light.dali_eg_vorraum_rgbw',
  'light.dali_eg_zimmer_1_rgbw',
  'light.dali_og_bad_rgbw',
  'light.dali_og_galerie_oben_rgbw',
  'light.dali_og_galerie_schattenfuge_rgbw',
  'light.dali_og_galerie_unten_rgbw',
  'light.dali_og_hobbyraum_rgbw',
  'light.dali_og_wohnzimmer_rgbw',
  'light.dali_og_zimmer_2_rgbw'
] %}
RED QUEEN 1.1 RGBW QUELL-STATUS (NUR LESEN)
{% for e in rgbw %}
{{ e }}:
  zustand: {{ states(e) }}
  unterstuetzte_farbmodi: {{ state_attr(e, 'supported_color_modes') }}
  aktueller_farbmodus: {{ state_attr(e, 'color_mode') }}
  helligkeit: {{ state_attr(e, 'brightness') }}
  rgbw_farbe: {{ state_attr(e, 'rgbw_color') }}
  rgb_farbe: {{ state_attr(e, 'rgb_color') }}
  unterstuetzte_funktionen: {{ state_attr(e, 'supported_features') }}
{% endfor %}
~~~

## Live-Ablesung nach isoliertem PASS

Alle 13 per Template geprüften Quellen light.dali_*_rgbw lieferten denselben Status:

- Zustand: off
- supported_color_modes: [ColorMode.RGBW]
- color_mode: None
- brightness: None
- rgbw_color: None
- rgb_color: None

Die 13 Quellen sind damit auf HA-Ebene als RGBW-fähig ausgewiesen.
Der ausgeschaltete Zustand erklärt fehlende aktive Farb-/Helligkeitswerte;
die erfolgreiche physische Farb- und Helligkeitsausgabe ist noch nicht belegt.

Ein Unit-Test sichert die Auswertung von HA-ColorMode.RGBW als StrEnum ab.

## Kontrollierter Praxistest mit genau einer Leuchte

Nur wenn es vor Ort gefahrlos und erwünscht ist:

1. In bestehendem Home Assistant light.dali_eg_buro_rgbw manuell auf rund 30 Prozent einschalten.
2. Über den nativen HA-Farbpicker eine gut erkennbare Farbe einstellen.
3. Physisch kontrollieren, ob sich Farbe und Helligkeit wie erwartet ändern.
4. Die read-only HA-Vorlage für diese Quelle im Zustand on erneut auslesen.
5. Den ursprünglichen Ausgangszustand (hier: off) wiederherstellen.

Keine Installation von Red Queen 1.1 im Produktivsystem;
kein automatischer Multi-Leuchten-Test und keine WAGO-Änderung.
Das bisherige Netzwerk-isolierte Staging kann keine physische Wirkung prüfen.

## Interpretation

- `supported_color_modes`: maßgeblich für die Freigabe der tatsächlichen Farbbefehle.
- `color_mode` / `rgbw_color`: nur lesbarer Zustand, kein Beleg für erfolgreiche Farbänderung.
- `None` oder `unavailable`: keine Farbfunktion annehmen; jeweilige Quelle nicht automatisch aktivieren.
- Keine zusätzlichen HA-Proxies im produktiven 1.0 erzeugen.

Danach folgen Code-Review der Guards und der kontrollierte Funktionstest nach Freigabe.