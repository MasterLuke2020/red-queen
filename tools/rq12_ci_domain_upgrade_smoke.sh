#!/usr/bin/env bash
# Two-boot synthetic-only HA domain upgrade test, NEVER for house configurations.
set -Eeuo pipefail
umask 077
[[ "$GITHUB_ACTIONS" == "true" ]] || { echo 'CI only, refusing' >&2; exit 2; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="ghcr.io/home-assistant/home-assistant:2026.9.2"
OLD_SHA="0e254503696f273ca1b6f48cdef1fb716ec4752f"
WORKDIR="$(mktemp -d /tmp/rq12-domain-ci.XXXXXXXX)"
NAME="rq12-ci-domain-$$"
RUNNING=0
cleanup() {
  if [[ "$RUNNING" == 1 ]]; then docker rm -f "$NAME" >/dev/null 2>&1 || true; fi
  if [[ "$WORKDIR" == /tmp/rq12-domain-ci.* ]]; then sudo rm -rf -- "$WORKDIR" || true; fi
}
trap cleanup EXIT

echo 'Fetching pinned old-domain revision for a synthetic test fixture'
git -C "$ROOT" fetch --no-tags --depth=1 origin "$OLD_SHA" >/dev/null
mkdir -p "$WORKDIR/old_repository" "$WORKDIR/old_config/custom_components"
git -C "$ROOT" archive "$OLD_SHA" custom_components/wnhf | tar -x -C "$WORKDIR/old_repository"
cp -a "$WORKDIR/old_repository/custom_components/wnhf" "$WORKDIR/old_config/custom_components/"
OLD_CONFIG="$WORKDIR/old_config"
NEW_CONFIG="$WORKDIR/new_config"
mkdir -p "$OLD_CONFIG/wnhf/house/registry"
cat > "$OLD_CONFIG/configuration.yaml" <<'YAML'
homeassistant:
  name: Red Queen CI Domain Upgrade
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
cat > "$OLD_CONFIG/wnhf/house/registry/rooms.yaml" <<'YAML'
building:
  id: house
  name: Synthetic CI House
rooms: []
YAML
printf 'lights: []\n' > "$OLD_CONFIG/wnhf/house/registry/lights.yaml"
printf 'covers: []\n' > "$OLD_CONFIG/wnhf/house/registry/covers.yaml"
printf 'openings: []\n' > "$OLD_CONFIG/wnhf/house/registry/openings.yaml"
printf 'plants: []\n' > "$OLD_CONFIG/wnhf/house/registry/plants.yaml"

boot_stop() {
  local config="$1" domain="$2" found=0 logs
  echo "Booting synthetic HA with domain $domain"
  sudo chown -R 0:0 "$config"
  sudo chmod 0700 "$config"
  docker run -d --name "$NAME" --pull always --user 0:0 \
    --network none --restart no --memory 1536m --cpus 2 \
    --security-opt no-new-privileges --cap-drop ALL \
    -v "$config:/config:rw" "$IMAGE" >/dev/null
  RUNNING=1
  for _attempt in $(seq 1 100); do
    logs="$(docker logs "$NAME" 2>&1 || true)"
    if grep -Fq 'Red Queen 1.1.0 started via config entry' <<< "$logs"; then
      found=1; break
    fi
    if [[ -f "$config/home-assistant.log" ]] &&
       sudo grep -Fq 'Red Queen 1.1.0 started via config entry' "$config/home-assistant.log"; then
      found=1; break
    fi
    if [[ "$(docker inspect -f '{{.State.Running}}' "$NAME")" != true ]]; then break; fi
    sleep 2
  done
  if [[ "$found" != 1 ]]; then
    docker logs "$NAME" 2>&1 | tail -n 100 >&2 || true
    echo "FAIL: synthetic HA boot for $domain" >&2
    exit 1
  fi
  sleep 5
  docker stop -t 20 "$NAME" >/dev/null
  docker rm "$NAME" >/dev/null
  RUNNING=0
  sudo chown -R "$(id -u):$(id -g)" "$config"
  echo "PASS: HA boot and shutdown for $domain"
}

boot_stop "$OLD_CONFIG" wnhf

# Explicitly exercise user-authored YAML and Lovelace service references.
cat > "$OLD_CONFIG/scripts.yaml" <<'YAML'
ci_test:
  sequence:
    - service: wnhf.smart_scene_activate
      target:
        entity_id: light.wnhf_existing_entity
YAML
mkdir -p "$OLD_CONFIG/.storage"
cat > "$OLD_CONFIG/.storage/lovelace.red-queen-ci" <<'JSON'
{"data":{"config":{"views":[{"cards":[{"tap_action":{"action":"call-service","service":"wnhf.lighting_all_off"},"entity":"light.wnhf_existing_entity"}]}]}}}
JSON

# Preserve original HA IDs in an external CI assertion file; never change source.
python3 - "$OLD_CONFIG" "$WORKDIR/expected.json" <<'PY'
import json
from pathlib import Path
import sys
old, expected_path = map(Path, sys.argv[1:])
entries = json.loads((old / ".storage/core.config_entries").read_text())["data"]["entries"]
entities = json.loads((old / ".storage/core.entity_registry").read_text())["data"]["entities"]
old_entries = [e for e in entries if e.get("domain") == "wnhf"]
assert len(old_entries) == 1
mapped = {e["unique_id"]: e["entity_id"] for e in entities if e.get("platform") == "wnhf"}
assert mapped
expected_path.write_text(json.dumps({"entry_id": old_entries[0]["entry_id"], "entity_ids": mapped}))
PY

# Exercise THE reusable copy-only staging tool rather than a separate inline
# implementation. It refuses existing targets, duplicate config entries and
# ambiguously described service calls.
python3 "$ROOT/tools/rq12_domain_stage.py" \
  --source "$OLD_CONFIG" --target "$NEW_CONFIG" \
  --package "$ROOT/custom_components/red_queen"

python3 - "$OLD_CONFIG" "$NEW_CONFIG" <<'PY'
import json
from pathlib import Path
import sys
old, new = map(Path, sys.argv[1:])
report = json.loads((new / "rq12_stage_report.json").read_text())
assert report["state"] == "STAGING_ONLY_NOT_PRODUCTION"
assert report["stats"]["entries"] == 1
assert report["stats"]["devices"] >= 1
assert report["stats"]["namespace_only_devices"] >= 1
assert report["stats"]["yaml_service_calls"] >= 1
assert report["stats"]["lovelace_service_calls"] >= 1
assert report["entity_ids_renamed"] == 0
assert (old / "scripts.yaml").read_text().find("wnhf.smart_scene_activate") >= 0
assert (new / "scripts.yaml").read_text().find("red_queen.smart_scene_activate") >= 0
assert (new / ".storage/lovelace.red-queen-ci").read_text().find(
    "red_queen.lighting_all_off") >= 0
assert (old / "custom_components/wnhf").is_dir()
assert not (new / "custom_components/wnhf").exists()
print("PASS: staged copy preserves original and rewrites only service calls")
PY

boot_stop "$NEW_CONFIG" red_queen
python3 - "$NEW_CONFIG" "$WORKDIR/expected.json" <<'PY'
from pathlib import Path
import json
import sys
root = Path(sys.argv[1])
expected_path = Path(sys.argv[2])
def read(name):
    return json.loads((root / ".storage" / name).read_text(encoding="utf-8"))
expected = json.loads(expected_path.read_text())
entries = read("core.config_entries")["data"]["entries"]
new = [e for e in entries if e.get("domain") == "red_queen"]
assert len(new) == 1 and new[0]["entry_id"] == expected["entry_id"]
assert all(e.get("domain") != "wnhf" for e in entries)
entities = read("core.entity_registry")["data"]["entities"]
actual = {e["unique_id"]: e["entity_id"] for e in entities
          if e.get("platform") == "red_queen"}
assert actual == expected["entity_ids"], "Entity registry identity changed"
assert not any(e.get("platform") == "wnhf" for e in entities)
devices = read("core.device_registry")["data"]["devices"]
namespaces = [pair[0] for dev in devices for pair in dev.get("identifiers", [])
              if isinstance(pair, list) and len(pair) == 2]
assert "red_queen" in namespaces and "wnhf" not in namespaces
print("PASS: original HA config entry reused under red_queen")
print("PASS: all original entity IDs and unique IDs reused without duplicate entities")
print("PASS: registered device ownership moved to red_queen")
print("PASS: zero PLC, Sonos, network, real hardware, or user configuration")
PY
