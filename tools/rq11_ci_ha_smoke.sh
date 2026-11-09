#!/usr/bin/env bash
# Red Queen 1.1.0 candidate: GitHub CI-only isolated Home Assistant smoke.
# Completely synthetic empty registries; no PLC, Sonos, tokens or production data.
set -Eeuo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="ghcr.io/home-assistant/home-assistant:2026.9.2"
NAME="rq11-ci-smoke-$$"
WORKDIR="$(mktemp -d /tmp/redqueen11-ci.XXXXXXXX)"
STAGE_STARTED=0

cleanup() {
  if [[ "$STAGE_STARTED" == 1 ]]; then
    docker rm -f "$NAME" >/dev/null 2>&1 || true
  fi
  if [[ -n "$WORKDIR" && "$WORKDIR" == /tmp/redqueen11-ci.* ]]; then
    sudo rm -rf -- "$WORKDIR" || true
  fi
}
trap cleanup EXIT

mkdir -p "$WORKDIR/config/custom_components" "$WORKDIR/config/wnhf/house/registry"
cp -a "$ROOT/custom_components/wnhf" "$WORKDIR/config/custom_components/wnhf"
# Execute native Configurator step definitions against the real HA selector APIs.
cp "$ROOT/tools/rq12_ci_editor_flow.py" "$WORKDIR/config/rq12_ci_editor_flow.py"
cat > "$WORKDIR/config/configuration.yaml" <<'YAML'
homeassistant:
  name: Red Queen CI Smoke
  time_zone: Europe/Vienna
http: {}
frontend: {}
lovelace: {}
wnhf: {}
logger:
  default: warning
  logs:
    custom_components.wnhf: info
YAML
cat > "$WORKDIR/config/wnhf/house/registry/rooms.yaml" <<'YAML'
building:
  id: house
  name: CI Test House
rooms: []
YAML
printf 'lights: []\n' > "$WORKDIR/config/wnhf/house/registry/lights.yaml"
printf 'covers: []\n' > "$WORKDIR/config/wnhf/house/registry/covers.yaml"
printf 'openings: []\n' > "$WORKDIR/config/wnhf/house/registry/openings.yaml"
printf 'plants: []\n' > "$WORKDIR/config/wnhf/house/registry/plants.yaml"

sudo chown -R 0:0 "$WORKDIR/config"
sudo chmod 0700 "$WORKDIR/config"
echo "Starting Home Assistant 2026.9.2 with synthetic registry; network NONE"
docker run -d --name "$NAME" --pull always \
  --user 0:0 --network none --restart no \
  --memory 1536m --cpus 2 \
  --security-opt no-new-privileges --cap-drop ALL \
  --volume "$WORKDIR/config:/config:rw" \
  "$IMAGE" >/dev/null
STAGE_STARTED=1
STARTED=0
for _attempt in $(seq 1 100); do
  LOGS="$(docker logs "$NAME" 2>&1 || true)"
  if grep -Fq 'Red Queen 1.1.0 started via config entry' <<< "$LOGS"; then
    STARTED=1
    break
  fi
  if [[ -f "$WORKDIR/config/home-assistant.log" ]] &&
     sudo grep -Fq 'Red Queen 1.1.0 started via config entry' \
       "$WORKDIR/config/home-assistant.log"; then
    STARTED=1
    break
  fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$NAME")" != "true" ]]; then
    break
  fi
  sleep 2
done
if [[ "$STARTED" != 1 ]]; then
  echo "Home Assistant 1.1 RC did not initialize" >&2
  docker logs "$NAME" 2>&1 | tail -n 120 >&2 || true
  if [[ -f "$WORKDIR/config/home-assistant.log" ]]; then
    sudo tail -n 120 "$WORKDIR/config/home-assistant.log" >&2 || true
  fi
  exit 1
fi
echo "Exercising Smart Lighting GUI dialogs with installed HA selector types"
docker exec -e PYTHONPATH=/config "$NAME" \
  python3 /config/rq12_ci_editor_flow.py
sleep 8
docker stop -t 20 "$NAME" >/dev/null
docker rm "$NAME" >/dev/null
STAGE_STARTED=0
sudo chown -R "$(id -u):$(id -g)" "$WORKDIR/config"
python3 - "$WORKDIR/config" <<'PY'
import json
from pathlib import Path
import sys

config = Path(sys.argv[1])
manifest = json.loads(
    (config / "custom_components/wnhf/manifest.json").read_text(encoding="utf-8")
)
assert manifest["version"] == "1.1.0", manifest["version"]
registry_path = config / ".storage/core.entity_registry"
assert registry_path.is_file(), "CI entity registry was not persisted"
registered = json.loads(registry_path.read_text(encoding="utf-8"))
entities = registered["data"]["entities"]
unique = {
    entity.get("unique_id") for entity in entities
    if entity.get("platform") == "wnhf"
}
required = {
    "wnhf_smart_living_house_mode",
    "wnhf_smart_message_text",
    "wnhf_smart_message_profile",
    "wnhf_smart_message_priority",
    "wnhf_smart_message_send",
}
missing = sorted(required - unique)
dupes = [
    e.get("entity_id") for e in entities
    if e.get("platform") == "wnhf"
    and str(e.get("unique_id", "")).startswith("wnhf_rgbw_")
]
assert not missing, f"Missing Smart Living entities: {missing}"
assert not dupes, f"Duplicate native RGBW entities: {dupes}"
print("PASS: isolated synthetic HA 2026.9.2 started RC 1.1.0")
print("PASS: all 5 Smart Living entities were registered")
print("PASS: zero duplicate RGBW proxies")
print("PASS: no network, live data or hardware available")
PY
