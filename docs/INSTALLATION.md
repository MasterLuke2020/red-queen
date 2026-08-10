# Installation and Lifecycle

## Home Assistant custom integration

Technical domain: `wnhf`

Expected integration directory inside the Home Assistant configuration tree:

```text
/config/custom_components/wnhf/
```

For the verified Docker installation used during RC1 development, the host-side path was:

```text
/opt/homeassistant/config/custom_components/wnhf/
```

## Single-instance config entry

The config flow allows one Red Queen config entry. Legacy `configuration.yaml` presence can be imported into that config entry; the public integration title is **Red Queen**.

## Full replace upgrade procedure

For development/RC replacement, the verified process is to stop Home Assistant, replace the complete `custom_components/wnhf` directory, remove stale `__pycache__` directories and start Home Assistant again.

Example for the verified Docker layout:

```bash
docker stop homeassistant
rm -rf /opt/homeassistant/config/custom_components/wnhf
# copy the complete wnhf directory from the release archive
find /opt/homeassistant/config/custom_components/wnhf -type d -name "__pycache__" -prune -exec rm -rf {} +
docker start homeassistant
```

## Startup lifecycle

On config-entry setup Red Queen:

1. prepares runtime services and persistent stores;
2. discovers providers;
3. loads the semantic registry;
4. falls back to recovery/safe mode if registry loading fails;
5. registers services and entity platforms;
6. schedules a delayed non-destructive registry validation;
7. exposes runtime diagnostics and release metadata.

## Unload/reload lifecycle

Config-entry unload removes the registered Red Queen services, cancels a still-pending startup validation callback, unloads provider discovery and drops the in-memory engine. A reload therefore creates a fresh runtime engine while persistent qualification evidence remains on disk.

This behavior was live-verified before RC1 release packaging.
