#!/usr/bin/env bash
# Red Queen 1.1: controlled 3-file hotfix, local rollback. No Restic changes.
set -Eeuo pipefail
umask 077

MODE="help"
PIN=""
if (( $# > 0 )); then MODE="$1"; fi
if (( $# > 1 )); then PIN="$2"; fi
BASE="c7bdaa30831260dd0236b5b1d29fc8930a2ae3f9"
BRANCH="feature/1.1.0-smart-living"
CONTAINER="homeassistant"
CONFIG="/srv/containers/homeassistant/config"
TARGET="$CONFIG/custom_components/wnhf"
ROLLROOT="/srv/containers/homeassistant/redqueen-rollbacks"
WORK=""
BACKUP=""
PREVIOUS=""
REPLACING=0

say() { printf '[RQ11-ALL-OFF] %s\n' "$*"; }
fail() { say "ABBRUCH: $*" >&2; exit 1; }
running() {
  [[ "$(sudo docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" == "true" ]]
}
restore_previous() {
  say "Aktualisierung unterbrochen: Wiederherstellung der vorherigen Dateien."
  if running; then sudo docker stop --time 45 "$CONTAINER" >/dev/null || true; fi
  for file in services.py smart_living_runtime.py dashboard_renderer.py; do
    sudo cp -a -- "$PREVIOUS/$file" "$TARGET/$file" || true
  done
  sudo docker start "$CONTAINER" >/dev/null || true
}
cleanup() {
  result=$?
  trap - EXIT
  if (( result != 0 && REPLACING == 1 )) && [[ -n "$PREVIOUS" ]]; then
    restore_previous
  fi
  if [[ -n "$WORK" && -d "$WORK" ]]; then rm -rf -- "$WORK"; fi
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

check_host() {
  for program in sudo docker python3 git mktemp cmp; do
    command -v "$program" >/dev/null || fail "Fehlendes Programm: $program"
  done
  sudo -v
  config_mount="$(sudo docker inspect -f '{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}' "$CONTAINER")"
  [[ "$config_mount" == "$CONFIG" ]] || fail "Docker /config Mount passt nicht zum Produktions-Preflight."
  installed="$(sudo python3 - "$TARGET/manifest.json" <<'PY'
import json,sys
with open(sys.argv[1],encoding="utf-8") as data:
    print(json.load(data)["version"])
PY
)"
  [[ "$installed" == "1.1.0" ]] || fail "Installierte Version nicht Red Queen 1.1.0."
}
start_checked() {
  sudo docker start "$CONTAINER" >/dev/null || fail "Home Assistant konnte nicht starten."
  sleep 12
  running || fail "Home Assistant Container ist nach Neustart nicht aktiv."
}

apply() {
  [[ "$PIN" =~ ^[0-9a-f]{40}$ ]] || fail "40-stelligen Git-Commit uebergeben."
  check_host
  running || fail "Home Assistant muss vor dem Upgrade laufen."
  WORK="$(mktemp -d)"
  say "Lade Zielcommit und bekannten Produktivstand."
  git clone --quiet --depth 1 --branch "$BRANCH" "https://github.com/MasterLuke2020/red-queen.git" "$WORK/repo" ||
    fail "GitHub Checkout fehlgeschlagen."
  head="$(git -C "$WORK/repo" rev-parse HEAD)"
  [[ "$head" == "$PIN" ]] ||
    fail "Entwicklungsbranch wurde geaendert: $head"
  git -C "$WORK/repo" fetch --quiet --depth 1 origin "$BASE" ||
    fail "Installierte Ausgangsrevision nicht abrufbar."
  mkdir "$WORK/baseline"
  for file in services.py smart_living_runtime.py dashboard_renderer.py; do
    git -C "$WORK/repo" show "$BASE:custom_components/wnhf/$file" > "$WORK/baseline/$file" ||
      fail "Basisdatei nicht geladen: $file"
    sudo cmp -s -- "$TARGET/$file" "$WORK/baseline/$file" ||
      fail "$file weicht vom installierten Ausgangsstand ab. Kein Patch."
    python3 -m py_compile "$WORK/repo/custom_components/wnhf/$file" ||
      fail "Syntaxpruefung fehlgeschlagen: $file"
  done

  sudo install -d -m 0700 "$ROLLROOT"
  BACKUP="$(sudo mktemp -d "$ROLLROOT/rq11-all-off-$(date +%Y%m%d-%H%M%S)-XXXXXXXX")"
  sudo install -d -m 0700 "$BACKUP/original"
  sudo install -d -m 0700 "$BACKUP/updated"
  for file in services.py smart_living_runtime.py dashboard_renderer.py; do
    sudo cp -a -- "$TARGET/$file" "$BACKUP/original/$file"
    sudo cp -a -- "$WORK/repo/custom_components/wnhf/$file" "$BACKUP/updated/$file"
  done
  PREVIOUS="$BACKUP/original"
  say "Nur Home Assistant wird gestoppt."
  sudo docker stop --time 45 "$CONTAINER" >/dev/null ||
    fail "Home Assistant Stop fehlgeschlagen."
  REPLACING=1
  for file in services.py smart_living_runtime.py dashboard_renderer.py; do
    sudo cp -a -- "$BACKUP/updated/$file" "$TARGET/$file"
  done
  start_checked
  printf '%s\n' "$BACKUP" | sudo tee "$ROLLROOT/last-rq11-all-off" >/dev/null
  sudo chmod 0600 "$ROLLROOT/last-rq11-all-off"
  REPLACING=0
  say "PATCH INSTALLIERT: Der globale Licht-Aus-Dienst umfasst nun DALI RGBW."
  say "Lokale Rueckfallsicherung: $BACKUP"
  say "Rueckweg: bash ~/rq11_all_off_patch.sh rollback"
  say "Container läuft. Funktion der Red Queen bitte im HA pruefen."
}

rollback() {
  check_host
  sudo test -f "$ROLLROOT/last-rq11-all-off" ||
    fail "Kein Rueckweg-Vermerk vorhanden."
  BACKUP="$(sudo cat "$ROLLROOT/last-rq11-all-off")"
  [[ "$BACKUP" == "$ROLLROOT"/rq11-all-off-* ]] ||
    fail "Unerwarteter Backup-Pfad."
  for file in services.py smart_living_runtime.py dashboard_renderer.py; do
    sudo test -f "$BACKUP/original/$file" ||
      fail "Backup Originaldatei fehlt: $file"
    sudo test -f "$BACKUP/updated/$file" ||
      fail "Backup Patchdatei fehlt: $file"
    sudo cmp -s -- "$TARGET/$file" "$BACKUP/updated/$file" ||
      fail "Installierte Datei $file wurde inzwischen veraendert: nichts ueberschrieben."
  done
  PREVIOUS="$BACKUP/updated"
  say "Stelle den bisherigen Red Queen 1.1.0 Stand wieder her."
  if running; then
    sudo docker stop --time 45 "$CONTAINER" >/dev/null ||
      fail "Home Assistant Stop fehlgeschlagen."
  fi
  REPLACING=1
  for file in services.py smart_living_runtime.py dashboard_renderer.py; do
    sudo cp -a -- "$BACKUP/original/$file" "$TARGET/$file"
  done
  start_checked
  REPLACING=0
  say "ROLLBACK OK: bisheriger 1.1.0-Stand wieder aktiv."
}

case "$MODE" in
  apply) apply ;;
  rollback) rollback ;;
  help|-h|--help)
    echo "Verwendung:"
    echo "  bash ~/rq11_all_off_patch.sh apply <40-stelliger-Git-Commit>"
    echo "  bash ~/rq11_all_off_patch.sh rollback"
    ;;
  *) fail "Unbekannte Aktion: $MODE" ;;
esac
