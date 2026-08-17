
"""Semantic notification-target model and optional registry loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class NotificationTargetRegistryError(ValueError):
    """Raised when notification_targets.yaml violates the RC6 contract."""


@dataclass(frozen=True, slots=True)
class NotificationTarget:
    """Provider-neutral semantic recipient target."""

    object_id: str
    name: str
    enabled: bool
    provider: str
    entity_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "enabled": self.enabled,
            "provider": self.provider,
            "entity_id": self.entity_id,
        }


def load_notification_targets(path: Path) -> dict[str, NotificationTarget]:
    """Load optional semantic notification targets; missing file is valid."""
    if not path.is_file():
        return {}

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as err:
        raise NotificationTargetRegistryError(
            f"Could not read {path}: {err}"
        ) from err

    if not isinstance(raw, dict):
        raise NotificationTargetRegistryError(
            "notification_targets.yaml root must be a dictionary."
        )
    items = raw.get("notification_targets")
    if not isinstance(items, list):
        raise NotificationTargetRegistryError(
            "'notification_targets' must be a list."
        )

    targets: dict[str, NotificationTarget] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise NotificationTargetRegistryError(
                f"Notification target #{index} must be a dictionary."
            )
        object_id = item.get("id")
        name = item.get("name")
        enabled = item.get("enabled", True)
        provider = item.get("provider")
        entity_id = item.get("entity_id")

        if not isinstance(object_id, str) or not object_id.strip():
            raise NotificationTargetRegistryError(
                f"Notification target #{index} has no valid 'id'."
            )
        if not object_id.startswith("notification.target."):
            raise NotificationTargetRegistryError(
                f"Notification target '{object_id}' must use the "
                "'notification.target.' prefix."
            )
        if object_id in targets:
            raise NotificationTargetRegistryError(
                f"Duplicate notification target id: {object_id}"
            )
        if not isinstance(name, str) or not name.strip():
            raise NotificationTargetRegistryError(
                f"Notification target '{object_id}' has no valid 'name'."
            )
        if not isinstance(enabled, bool):
            raise NotificationTargetRegistryError(
                f"Notification target '{object_id}': enabled must be boolean."
            )
        if provider != "home_assistant_notify_entity":
            raise NotificationTargetRegistryError(
                f"Notification target '{object_id}' has unsupported provider "
                f"{provider!r}."
            )
        if (
            not isinstance(entity_id, str)
            or not entity_id.startswith("notify.")
            or len(entity_id) <= len("notify.")
        ):
            raise NotificationTargetRegistryError(
                f"Notification target '{object_id}' has invalid notify entity_id."
            )

        targets[object_id] = NotificationTarget(
            object_id=object_id,
            name=name.strip(),
            enabled=enabled,
            provider=provider,
            entity_id=entity_id,
        )
    return targets
