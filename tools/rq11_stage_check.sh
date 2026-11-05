#!/usr/bin/env bash
# Red Queen 1.1 – isolated Home Assistant staging smoke test.
# NEVER loads a production writable mount, publishes ports, or joins the LAN.
set -Eeuo pipefail
umask 077

REPOSITORY="https://github.com/MasterLuke2020/red-queen.git"
BRANCH="feature/1.1.0-smart-living"
PRODUCTION_CONTAINER="homeassistant"
CONTAINER_NAME="rq11-stage-$$"
STAGE_STARTED=0
STAGE_OK=0

log() { printf '[RQ11] %s\n' "$*"; }
fail() { printf '[RQ11 ERROR] %s\n' "$*" >&2; exit 1; }
docker_cmd() { sudo docker "$@"; }
cleanup() {
  if [[ "$STAGE_STARTED" == "1" ]]; then
    docker_cmd rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

command -v git >/dev/null || fail "git not installed"
command -v python3 >/dev/null || fail "python3 not installed"
command -v sudo >/dev/null || fail "sudo not installed"
command -v grep >/dev/null || fail "grep not installed"
sudo -v || fail "sudo authentication failed"
docker_cmd info >/dev/null || fail "Docker daemon inaccessible"
docker_cmd inspect "$PRODUCTION_CONTAINER" >/dev/null 2>&1 ||
  fail "Home Assistant production container not found: $PRODUCTION_CONTAINER"

PROD_RUNNING="$(docker_cmd inspect -f '{{.State.Running}}' "$PRODUCTION_CONTAINER")"
[[ "$PROD_RUNNING" == "true" ]] || fail "Production Home Assistant is not running"

IMAGE="$(docker_cmd inspect -f '{{.Config.Image}}' "$PRODUCTION_CONTAINER")"
docker_cmd image inspect "$IMAGE" >/dev/null ||
  fail "Home Assistant image unavailable locally: $IMAGE"

WORKDIR="$(mktemp -d "/tmp/redqueen11-stage.XXXXXXXX")"
mkdir -p "$WORKDIR/config/custom_components" "$WORKDIR/config/wnhf/house/registry"
log "Isolated files under $WORKDIR"
log "Production status: RUNNING (will not restart/stop/modify)"
log "Cloning only the Red Queen DEVELOPMENT branch"
git clone --quiet --depth 1 --single-branch --branch "$BRANCH" "$REPOSITORY" \
  "$WORKDIR/source" || fail "Could not clone development branch"

REVISION="$(git -C "$WORKDIR/source" rev-parse HEAD)"
log "GitHub source: $REVISION"

# docker cp never writes to its source container.
log "Copying house registry READ-ONLY from the running HA container"
docker_cmd cp "$PRODUCTION_CONTAINER:/config/wnhf/house/registry/." \
  "$WORKDIR/config/wnhf/house/registry/" ||
  fail "Could not read the Red Queen house registry"

# The stage never receives HA secrets, auth, config entries, automations or LAN.
cp -a "$WORKDIR/source/custom_components/wnhf" \
  "$WORKDIR/config/custom_components/wnhf"
cat > "$WORKDIR/config/configuration.yaml" <<'YAML'
homeassistant:
  name: Red Queen Isolated Staging
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

log "Starting isolated HA (network=none, no published ports, memory limited)"
docker_cmd run --detach --pull never \
  --name "$CONTAINER_NAME" \
  --network none \
  --restart no \
  --memory 1152m --cpus 1.5 \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --volume "$WORKDIR/config:/config:rw" \
  "$IMAGE" >/dev/null || fail "Could not start isolated stage"
STAGE_STARTED=1

log "Checking HA initialization and Red Queen native integration setup"
for _attempt in $(seq 1 80); do
  if [[ -f "$WORKDIR/config/home-assistant.log" ]] &&
     grep -Fq "started via config entry" "$WORKDIR/config/home-assistant.log"; then
    STAGE_OK=1
    break
  fi
  if docker_cmd logs "$CONTAINER_NAME" 2>&1 |
     grep -Fq "started via config entry"; then
    STAGE_OK=1
    break
  fi
  RUNNING="$(docker_cmd inspect -f '{{.State.Running}}' "$CONTAINER_NAME")"
  [[ "$RUNNING" == "true" ]] || break
  sleep 2
done

# Allow Home Assistant to persist the stage-only entity registry.
if [[ "$STAGE_OK" == "1" ]]; then
  sleep 8
fi
docker_cmd logs "$CONTAINER_NAME" > "$WORKDIR/staging-docker.log" 2>&1 || true
docker_cmd stop --time 15 "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker_cmd rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
STAGE_STARTED=0

# Only the isolated directory is chowned, after its staging container is gone.
# Home Assistant may have created root-only files under its private .storage.
sudo chown -R "$(id -u):$(id -g)" "$WORKDIR/config" ||
  fail "Unable to read isolated staging output"

# Produce a compact machine-readable report; full logs stay on the server.
python3 - "$WORKDIR" "$REVISION" "$IMAGE" "$STAGE_OK" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
revision, image, setup_flag = sys.argv[2:]
registry = root / "config/.storage/core.entity_registry"
entities = []
warnings = []
if registry.is_file():
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
        entities = data.get("data", {}).get("entities", [])
    except (OSError, ValueError, TypeError):
        warnings.append("Isolated entity registry unreadable")
else:
    warnings.append("Isolated entity registry not yet persisted")
required = {
    "house_mode": "wnhf_smart_living_house_mode",
    "message_text": "wnhf_smart_message_text",
    "message_profile": "wnhf_smart_message_profile",
    "message_priority": "wnhf_smart_message_priority",
    "message_send": "wnhf_smart_message_send",
}
actual = {x.get("unique_id"): x.get("entity_id") for x in entities
          if isinstance(x, dict) and x.get("platform") == "wnhf"}
check = {key: actual.get(uid) for key, uid in required.items()}
pass_setup = setup_flag == "1"
report = {
    "schema": "rq11.isolated_smoke.v1",
    "development_commit": revision,
    "image": image,
    "production_modified": False,
    "isolated_stage_no_network": True,
    "isolated_stage_no_production_mount": True,
    "stage_entry_setup_observed": pass_setup,
    "new_native_entity_ids": check,
    "new_native_entities_resolved": all(check.values()),
    "status": "PASS" if pass_setup and all(check.values()) else "INCOMPLETE",
    "warnings": warnings,
    "limitations": [
        "No access to WAGO, Sonos, actual RGBW states or external services",
        "Stage tests HA import and entity registration, not physical commands",
        "Stage uses its own config and registry copy only",
    ],
}
report_path = root / "redqueen11_staging_report.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
print("[RQ11] Report: " + str(report_path))
print("[RQ11] Status: " + report["status"])
print("[RQ11] Entity registration:")
for key, value in check.items():
    print("[RQ11]   " + key + ": " + (value or "NOT FOUND"))
if not pass_setup:
    print("[RQ11] Red Queen setup marker missing – local stage log: " +
          str(root / "config/home-assistant.log"))
PY

log "Original HA remains running; staging container removed."
log "Review redqueen11_staging_report.json before uploading it."
RESULT_STATUS="$(python3 - "$WORKDIR/redqueen11_staging_report.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as file:
    print(json.load(file)["status"])
PY
)"
if [[ "$RESULT_STATUS" != "PASS" ]]; then
  fail "Isolated smoke incomplete. Share only the redqueen11_staging_report.json report; keep logs local."
fi
