#!/usr/bin/env bash
# Red Queen 1.1 RC -- commit-pinned integration-only upgrade or rollback.
# No Restic, PLC, Sonos, Docker Compose edits or other integration changes.
set -Eeuo pipefail
umask 077

MODE="help"
PIN=""
if (( $# > 0 )); then MODE="$1"; fi
if (( $# > 1 )); then PIN="$2"; fi
CONTAINER="homeassistant"
CONFIG="/srv/containers/homeassistant/config"
TARGET="$CONFIG/custom_components/wnhf"
ROLLROOT="/srv/containers/homeassistant/redqueen-rollbacks"
UPSTREAM="https://github.com/MasterLuke2020/red-queen.git"
BRANCH="feature/1.1.0-smart-living"
EXPECTED_MANIFEST="9cfded727c17f20377ee46adf5a711fd505c8d63edd082941ef4fa62414aeaec"
EXPECTED_RELEASE="4a1740bbc77a288cefa46a8854d1d77001e4ddcab58c50b2b034d1cf96fe34c2"

WORK=""
STAGE=""
BACKUP=""
STOPPED=0
OLD_MOVED=0
NEW_MOVED=0
DONE=0
say() { printf '[RQ11] %s\n' "$*"; }
fail() { say "ABBRUCH: $*" >&2; exit 1; }
running() {
  [[ "$(sudo docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" == "true" ]]
}
version() {
  sudo python3 - "$1" <<'PY'
import json,sys
with open(sys.argv[1],encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
}
recover_interrupted() {
  say "Stelle Originalversion aus lokalem Rueckweg wieder her."
  if [[ "$NEW_MOVED" == 1 && -d "$TARGET" ]]; then
    sudo mv -- "$TARGET" "$BACKUP/wnhf-interrupted" || true
  fi
  if [[ "$OLD_MOVED" == 1 && -d "$BACKUP/wnhf-1.0.0" && ! -e "$TARGET" ]]; then
    sudo mv -- "$BACKUP/wnhf-1.0.0" "$TARGET" || true
  fi
  if [[ "$STOPPED" == 1 ]]; then
    sudo docker start "$CONTAINER" >/dev/null || true
  fi
}
cleanup() {
  code=$?
  trap - EXIT
  if (( code != 0 && STOPPED == 1 )); then recover_interrupted; fi
  if [[ -n "$STAGE" && -e "$STAGE" ]]; then sudo rm -rf -- "$STAGE"; fi
  if [[ -n "$WORK" && -d "$WORK" ]]; then rm -rf -- "$WORK"; fi
  exit "$code"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

check_host() {
  for tool in sudo docker python3 sha256sum date mktemp; do
    command -v "$tool" >/dev/null || fail "Fehlendes Programm: $tool"
  done
  sudo -v
  running || fail "Produktiver Container laeuft nicht."
  mount="$(sudo docker inspect -f '{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}' "$CONTAINER")"
  [[ "$mount" == "$CONFIG" ]] || fail "Unerwarteter Docker-/config-Mount: $mount"
  sudo test -f "$TARGET/manifest.json" || fail "Installierte Red Queen nicht gefunden."
}

check_baseline() {
  [[ "$(version "$TARGET/manifest.json")" == "1.0.0" ]] ||
    fail "Es ist nicht mehr Version 1.0.0 installiert."
  [[ "$(version "$TARGET/RELEASE.json")" == "1.0.0" ]] ||
    fail "Unpassende alte RELEASE.json."
  manifest_sha="$(sudo sha256sum "$TARGET/manifest.json" | cut -d' ' -f1)"
  release_sha="$(sudo sha256sum "$TARGET/RELEASE.json" | cut -d' ' -f1)"
  [[ "$manifest_sha" == "$EXPECTED_MANIFEST" && "$release_sha" == "$EXPECTED_RELEASE" ]] ||
    fail "Aktuelle 1.0.0-Metadaten weichen vom lesenden Produktions-Preflight ab."
}

start_checked() {
  sudo docker start "$CONTAINER" >/dev/null ||
    fail "Docker konnte Home Assistant nicht starten."
  for i in $(seq 1 12); do
    sleep 2
    running || fail "Home Assistant Container ist nach Neustart beendet."
  done
  STOPPED=0
}

upgrade() {
  [[ "$PIN" =~ ^[0-9a-f]{40}$ ]] || fail "Exakten 40-stelligen Git-Commit angeben."
  command -v git >/dev/null || fail "Git fehlt."
  check_host
  check_baseline

  say "Lade und pruefe freigegebenen Commit $PIN."
  WORK="$(mktemp -d)"
  git clone --quiet --depth 1 --branch "$BRANCH" "$UPSTREAM" "$WORK/repo" ||
    fail "Git-Download nicht moeglich."
  head="$(git -C "$WORK/repo" rev-parse HEAD)"
  [[ "$head" == "$PIN" ]] ||
    fail "Branch hat sich seit der Freigabe geaendert: $head (keine Installation)."
  source_dir="$WORK/repo/custom_components/wnhf"
  [[ -d "$source_dir" ]] || fail "Integration fehlt in Git-Checkout."
  [[ "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["version"])' "$source_dir/manifest.json")" == "1.1.0" ]] ||
    fail "Falsche Kandidatenversion."
  python3 - "$source_dir/RELEASE.json" <<'PY' || fail "Kein passender 1.1.0-RC."
import json,sys
with open(sys.argv[1],encoding="utf-8") as f:
    d=json.load(f)
assert (d.get("version"),d.get("channel"),d.get("phase"),d.get("candidate_status")) == (
    "1.1.0","candidate","rc","development"), "RC-Status passt nicht"
PY

  sudo install -d -m 0700 "$ROLLROOT"
  BACKUP="$(sudo mktemp -d "$ROLLROOT/pre-11-$(date +%Y%m%d-%H%M%S)-XXXXXXXX")"
  STAGE="$CONFIG/custom_components/.rq11-stage-$(date +%s)-$$"
  sudo cp -a -- "$source_dir" "$STAGE"
  [[ "$(version "$STAGE/manifest.json")" == "1.1.0" ]] ||
    fail "Unvollstaendige Stage-Integration."
  say "RC bereitgestellt; bestehende Home-Assistant-Instanz wird angehalten."
  sudo docker stop --time 45 "$CONTAINER" >/dev/null ||
    fail "Home Assistant konnte nicht angehalten werden."
  STOPPED=1

  sudo mkdir -m 0700 "$BACKUP/ha-registry-before"
  for item in core.entity_registry core.device_registry core.config_entries; do
    if sudo test -f "$CONFIG/.storage/$item"; then
      sudo cp -a -- "$CONFIG/.storage/$item" "$BACKUP/ha-registry-before/$item"
    fi
  done
  if sudo test -d "$CONFIG/wnhf"; then
    sudo cp -a -- "$CONFIG/wnhf" "$BACKUP/wnhf-config-before"
  fi

  sudo mv -- "$TARGET" "$BACKUP/wnhf-1.0.0"
  OLD_MOVED=1
  sudo mv -- "$STAGE" "$TARGET"
  STAGE=""
  NEW_MOVED=1
  say "Integration getauscht; starte den bestehenden Docker-Container."
  start_checked
  [[ "$(version "$TARGET/manifest.json")" == "1.1.0" ]] ||
    fail "Manifest ist nach Upgrade nicht 1.1.0."
  printf '%s\n' "$BACKUP" | sudo tee "$ROLLROOT/last-upgrade" >/dev/null
  sudo chmod 0600 "$ROLLROOT/last-upgrade"
  DONE=1
  say "INSTALLATION OK: Red Queen 1.1.0, Git-Commit $PIN."
  say "Ausgangsversion gesichert unter: $BACKUP/wnhf-1.0.0"
  say "Falls Red Queen in HA nicht korrekt startet: bash ~/rq11_deploy.sh rollback"
  say "Container läuft; HA-Integration und Hardware jetzt bitte im Praxistest prüfen."
}

rollback() {
  check_host
  [[ "$(version "$TARGET/manifest.json")" == "1.1.0" ]] ||
    fail "Keine Red Queen 1.1.0 installiert."
  sudo test -f "$ROLLROOT/last-upgrade" ||
    fail "Lokales Rueckwegverzeichnis nicht vermerkt."
  BACKUP="$(sudo cat "$ROLLROOT/last-upgrade")"
  [[ "$BACKUP" == "$ROLLROOT"/pre-11-* ]] ||
    fail "Rueckwegverzeichnis liegt ausserhalb des erwarteten Pfads."
  sudo test -d "$BACKUP/wnhf-1.0.0" || fail "Gesicherte 1.0.0 fehlt."
  [[ "$(version "$BACKUP/wnhf-1.0.0/manifest.json")" == "1.0.0" ]] ||
    fail "Gesicherte Dateien sind nicht Version 1.0.0."
  STAGE="$CONFIG/custom_components/.rq11-rollback-$(date +%s)-$$"
  sudo cp -a -- "$BACKUP/wnhf-1.0.0" "$STAGE"
  say "Originaldateien 1.0.0 bereitgestellt; stoppe HA."
  sudo docker stop --time 45 "$CONTAINER" >/dev/null ||
    fail "Home Assistant konnte nicht gestoppt werden."
  STOPPED=1
  sudo mv -- "$TARGET" "$BACKUP/wnhf-1.1.0-after-rollback"
  NEW_MOVED=1
  sudo mv -- "$STAGE" "$TARGET"
  STAGE=""
  start_checked
  [[ "$(version "$TARGET/manifest.json")" == "1.0.0" ]] ||
    fail "Rueckweg-Manifest ungueltig."
  say "ROLLBACK OK: Red Queen 1.0.0 wiederhergestellt."
  say "Die gesicherten HA-Registry-Dateien bleiben nur als lokale Reserve, unveraendert."
}

case "$MODE" in
  install) upgrade ;;
  rollback) rollback ;;
  help|-h|--help)
    printf '%s\n' "Benutzung:" \
      "  bash ~/rq11_deploy.sh install <genauer-40-stelliger-Git-Commit>" \
      "  bash ~/rq11_deploy.sh rollback" \
      "Ohne Restic-Write, PLC-, Sonos- oder Docker-Compose-Aenderungen."
    ;;
  *) fail "Unbekannter Befehl '$MODE'." ;;
esac
