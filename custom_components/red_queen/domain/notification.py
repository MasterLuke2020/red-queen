"""Semantic notification, announcement and routing registry models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


NOTIFICATION_PRIORITIES = ("debug", "info", "warning", "critical")
NOTIFICATION_PROFILES = ("standard", "silent", "voice", "mobile", "broadcast")
ANNOUNCEMENT_LEVELS = ("info", "notice", "warning", "alarm")


class NotificationTargetRegistryError(ValueError):
    """Raised when notification_targets.yaml violates the public contract."""


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


@dataclass(frozen=True, slots=True)
class AnnouncementLevelProfile:
    """Installation-owned playback settings for one semantic urgency level."""

    level: str
    speaker_entity_ids: tuple[str, ...]
    volume: float
    prefix: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "speaker_entity_ids": list(self.speaker_entity_ids),
            "volume": self.volume,
            "prefix": self.prefix,
        }


@dataclass(frozen=True, slots=True)
class AnnouncementTarget:
    """Provider-neutral semantic announcement route."""

    object_id: str
    name: str
    enabled: bool
    provider: str
    tts_entity_id: str
    cache: bool
    with_group: bool
    seconds_per_word: float
    padding_seconds: float
    minimum_seconds: int
    maximum_seconds: int
    levels: dict[str, AnnouncementLevelProfile]

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "enabled": self.enabled,
            "provider": self.provider,
            "tts_entity_id": self.tts_entity_id,
            "cache": self.cache,
            "with_group": self.with_group,
            "duration": {
                "seconds_per_word": self.seconds_per_word,
                "padding_seconds": self.padding_seconds,
                "minimum_seconds": self.minimum_seconds,
                "maximum_seconds": self.maximum_seconds,
            },
            "levels": {
                level: self.levels[level].as_dict()
                for level in ANNOUNCEMENT_LEVELS
            },
        }


@dataclass(frozen=True, slots=True)
class NotificationRoute:
    """Semantic fan-out configuration for one installation."""

    object_id: str
    name: str
    enabled: bool
    notification_target_ids: tuple[str, ...]
    announcement_target_id: str | None
    log_enabled: bool
    dashboard_enabled: bool
    quiet_mode_entity_id: str | None
    house_state_entity_id: str | None
    voice_blocked_states: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "enabled": self.enabled,
            "notification_target_ids": list(self.notification_target_ids),
            "announcement_target_id": self.announcement_target_id,
            "log_enabled": self.log_enabled,
            "dashboard_enabled": self.dashboard_enabled,
            "context": {
                "quiet_mode_entity_id": self.quiet_mode_entity_id,
                "house_state_entity_id": self.house_state_entity_id,
                "voice_blocked_states": list(self.voice_blocked_states),
            },
        }


@dataclass(frozen=True, slots=True)
class NotificationRegistry:
    """Complete optional notification configuration for one installation."""

    notification_targets: dict[str, NotificationTarget]
    announcement_targets: dict[str, AnnouncementTarget]
    notification_routes: dict[str, NotificationRoute]


def _read_registry(path: Path) -> dict[str, Any]:
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
    return raw


def _items(raw: dict[str, Any], key: str) -> list[Any]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        raise NotificationTargetRegistryError(f"'{key}' must be a list.")
    return value


def _required_id(
    item: dict[str, Any], *, index: int, prefix: str, kind: str
) -> str:
    object_id = item.get("id")
    if not isinstance(object_id, str) or not object_id.strip():
        raise NotificationTargetRegistryError(
            f"{kind} #{index} has no valid 'id'."
        )
    object_id = object_id.strip()
    if not object_id.startswith(prefix):
        raise NotificationTargetRegistryError(
            f"{kind} '{object_id}' must use the '{prefix}' prefix."
        )
    return object_id


def _required_name(item: dict[str, Any], *, object_id: str) -> str:
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        raise NotificationTargetRegistryError(
            f"Target '{object_id}' has no valid 'name'."
        )
    return name.strip()


def _enabled(item: dict[str, Any], *, object_id: str) -> bool:
    enabled = item.get("enabled", True)
    if not isinstance(enabled, bool):
        raise NotificationTargetRegistryError(
            f"Target '{object_id}': enabled must be boolean."
        )
    return enabled


def _entity_id(
    value: Any, *, object_id: str, field: str, domain: str | None = None
) -> str:
    if not isinstance(value, str) or not value.strip() or "." not in value:
        raise NotificationTargetRegistryError(
            f"Target '{object_id}' has invalid {field}."
        )
    value = value.strip()
    if domain is not None and not value.startswith(f"{domain}."):
        raise NotificationTargetRegistryError(
            f"Target '{object_id}' {field} must reference {domain}.*."
        )
    return value


def _optional_entity_id(
    value: Any, *, object_id: str, field: str
) -> str | None:
    if value is None:
        return None
    return _entity_id(value, object_id=object_id, field=field)


def _string_list(
    value: Any,
    *,
    object_id: str,
    field: str,
    prefix: str | None = None,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise NotificationTargetRegistryError(
            f"Target '{object_id}' {field} must be a list."
        )
    result: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry.strip():
            raise NotificationTargetRegistryError(
                f"Target '{object_id}' {field} contains an invalid value."
            )
        entry = entry.strip()
        if prefix is not None and not entry.startswith(prefix):
            raise NotificationTargetRegistryError(
                f"Target '{object_id}' {field} value '{entry}' "
                f"must use prefix '{prefix}'."
            )
        if entry not in result:
            result.append(entry)
    return tuple(result)


def _notification_targets(
    raw: dict[str, Any],
) -> dict[str, NotificationTarget]:
    targets: dict[str, NotificationTarget] = {}
    for index, item in enumerate(
        _items(raw, "notification_targets"), start=1
    ):
        if not isinstance(item, dict):
            raise NotificationTargetRegistryError(
                f"Notification target #{index} must be a dictionary."
            )
        object_id = _required_id(
            item,
            index=index,
            prefix="notification.target.",
            kind="Notification target",
        )
        if object_id in targets:
            raise NotificationTargetRegistryError(
                f"Duplicate notification target id: {object_id}"
            )
        provider = item.get("provider")
        if provider != "home_assistant_notify_entity":
            raise NotificationTargetRegistryError(
                f"Notification target '{object_id}' has unsupported provider "
                f"{provider!r}."
            )
        targets[object_id] = NotificationTarget(
            object_id=object_id,
            name=_required_name(item, object_id=object_id),
            enabled=_enabled(item, object_id=object_id),
            provider=provider,
            entity_id=_entity_id(
                item.get("entity_id"),
                object_id=object_id,
                field="entity_id",
                domain="notify",
            ),
        )
    return targets


def _announcement_targets(
    raw: dict[str, Any],
) -> dict[str, AnnouncementTarget]:
    targets: dict[str, AnnouncementTarget] = {}
    default_prefixes = {
        "info": None,
        "notice": "Hinweis.",
        "warning": "Warnung.",
        "alarm": "Achtung!",
    }
    for index, item in enumerate(
        _items(raw, "announcement_targets"), start=1
    ):
        if not isinstance(item, dict):
            raise NotificationTargetRegistryError(
                f"Announcement target #{index} must be a dictionary."
            )
        object_id = _required_id(
            item,
            index=index,
            prefix="announcement.target.",
            kind="Announcement target",
        )
        if object_id in targets:
            raise NotificationTargetRegistryError(
                f"Duplicate announcement target id: {object_id}"
            )
        provider = item.get("provider")
        if provider not in {
            "home_assistant_tts",
            "home_assistant_tts_sonos",
        }:
            raise NotificationTargetRegistryError(
                f"Announcement target '{object_id}' has unsupported provider "
                f"{provider!r}."
            )
        cache = item.get("cache", False)
        with_group = item.get("with_group", True)
        if not isinstance(cache, bool) or not isinstance(with_group, bool):
            raise NotificationTargetRegistryError(
                f"Announcement target '{object_id}' cache/with_group must be "
                "boolean."
            )
        duration = item.get("duration", {})
        if not isinstance(duration, dict):
            raise NotificationTargetRegistryError(
                f"Announcement target '{object_id}' duration must be a "
                "dictionary."
            )
        seconds_per_word = duration.get("seconds_per_word", 0.45)
        padding_seconds = duration.get("padding_seconds", 3.0)
        minimum_seconds = duration.get("minimum_seconds", 5)
        maximum_seconds = duration.get("maximum_seconds", 90)
        numeric_values = (
            seconds_per_word,
            padding_seconds,
            minimum_seconds,
            maximum_seconds,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in numeric_values
        ):
            raise NotificationTargetRegistryError(
                f"Announcement target '{object_id}' duration values must be "
                "numeric."
            )
        if (
            seconds_per_word <= 0
            or padding_seconds < 0
            or minimum_seconds < 0
            or maximum_seconds < minimum_seconds
        ):
            raise NotificationTargetRegistryError(
                f"Announcement target '{object_id}' duration bounds are invalid."
            )
        raw_levels = item.get("levels")
        if not isinstance(raw_levels, dict):
            raise NotificationTargetRegistryError(
                f"Announcement target '{object_id}' levels must be a dictionary."
            )
        if set(raw_levels) != set(ANNOUNCEMENT_LEVELS):
            raise NotificationTargetRegistryError(
                f"Announcement target '{object_id}' must define exactly: "
                + ", ".join(ANNOUNCEMENT_LEVELS)
                + "."
            )
        levels: dict[str, AnnouncementLevelProfile] = {}
        for level in ANNOUNCEMENT_LEVELS:
            raw_level = raw_levels[level]
            if not isinstance(raw_level, dict):
                raise NotificationTargetRegistryError(
                    f"Announcement target '{object_id}' level '{level}' must "
                    "be a dictionary."
                )
            speakers = _string_list(
                raw_level.get("speakers"),
                object_id=object_id,
                field=f"levels.{level}.speakers",
                prefix="media_player.",
            )
            if not speakers:
                raise NotificationTargetRegistryError(
                    f"Announcement target '{object_id}' level '{level}' "
                    "needs speakers."
                )
            volume = raw_level.get("volume")
            if (
                isinstance(volume, bool)
                or not isinstance(volume, (int, float))
                or not 0 <= volume <= 1
            ):
                raise NotificationTargetRegistryError(
                    f"Announcement target '{object_id}' level '{level}' "
                    "volume must be 0..1."
                )
            prefix = raw_level.get("prefix", default_prefixes[level])
            if prefix is not None and (
                not isinstance(prefix, str) or not prefix.strip()
            ):
                raise NotificationTargetRegistryError(
                    f"Announcement target '{object_id}' level '{level}' "
                    "prefix must be string/null."
                )
            levels[level] = AnnouncementLevelProfile(
                level=level,
                speaker_entity_ids=speakers,
                volume=float(volume),
                prefix=prefix.strip() if isinstance(prefix, str) else None,
            )
        targets[object_id] = AnnouncementTarget(
            object_id=object_id,
            name=_required_name(item, object_id=object_id),
            enabled=_enabled(item, object_id=object_id),
            provider=provider,
            tts_entity_id=_entity_id(
                item.get("tts_entity_id"),
                object_id=object_id,
                field="tts_entity_id",
                domain="tts",
            ),
            cache=cache,
            with_group=with_group,
            seconds_per_word=float(seconds_per_word),
            padding_seconds=float(padding_seconds),
            minimum_seconds=int(minimum_seconds),
            maximum_seconds=int(maximum_seconds),
            levels=levels,
        )
    return targets


def _notification_routes(
    raw: dict[str, Any],
) -> dict[str, NotificationRoute]:
    routes: dict[str, NotificationRoute] = {}
    for index, item in enumerate(
        _items(raw, "notification_routes"), start=1
    ):
        if not isinstance(item, dict):
            raise NotificationTargetRegistryError(
                f"Notification route #{index} must be a dictionary."
            )
        object_id = _required_id(
            item,
            index=index,
            prefix="notification.route.",
            kind="Notification route",
        )
        if object_id in routes:
            raise NotificationTargetRegistryError(
                f"Duplicate notification route id: {object_id}"
            )
        notification_target_ids = _string_list(
            item.get("notification_target_ids", []),
            object_id=object_id,
            field="notification_target_ids",
            prefix="notification.target.",
        )
        announcement_target_id = item.get("announcement_target_id")
        if announcement_target_id is not None:
            if (
                not isinstance(announcement_target_id, str)
                or not announcement_target_id.startswith(
                    "announcement.target."
                )
            ):
                raise NotificationTargetRegistryError(
                    f"Notification route '{object_id}' has invalid "
                    "announcement_target_id."
                )
            announcement_target_id = announcement_target_id.strip()
        log_enabled = item.get("log_enabled", True)
        dashboard_enabled = item.get("dashboard_enabled", True)
        if not isinstance(log_enabled, bool) or not isinstance(
            dashboard_enabled, bool
        ):
            raise NotificationTargetRegistryError(
                f"Notification route '{object_id}' channel flags must be "
                "boolean."
            )
        context = item.get("context", {})
        if not isinstance(context, dict):
            raise NotificationTargetRegistryError(
                f"Notification route '{object_id}' context must be a dictionary."
            )
        blocked_states = _string_list(
            context.get(
                "voice_blocked_states",
                ["away", "vacation", "unknown", "unavailable"],
            ),
            object_id=object_id,
            field="context.voice_blocked_states",
        )
        routes[object_id] = NotificationRoute(
            object_id=object_id,
            name=_required_name(item, object_id=object_id),
            enabled=_enabled(item, object_id=object_id),
            notification_target_ids=notification_target_ids,
            announcement_target_id=announcement_target_id,
            log_enabled=log_enabled,
            dashboard_enabled=dashboard_enabled,
            quiet_mode_entity_id=_optional_entity_id(
                context.get("quiet_mode_entity_id"),
                object_id=object_id,
                field="context.quiet_mode_entity_id",
            ),
            house_state_entity_id=_optional_entity_id(
                context.get("house_state_entity_id"),
                object_id=object_id,
                field="context.house_state_entity_id",
            ),
            voice_blocked_states=blocked_states,
        )
    return routes


def load_notification_registry(path: Path) -> NotificationRegistry:
    """Load all optional notification registry sections."""
    raw = _read_registry(path)
    notification_targets = _notification_targets(raw)
    announcement_targets = _announcement_targets(raw)
    notification_routes = _notification_routes(raw)

    for route in notification_routes.values():
        missing_notifications = set(route.notification_target_ids) - set(
            notification_targets
        )
        if missing_notifications:
            raise NotificationTargetRegistryError(
                f"Notification route '{route.object_id}' references unknown "
                "notification target(s): "
                + ", ".join(sorted(missing_notifications))
                + "."
            )
        if (
            route.announcement_target_id is not None
            and route.announcement_target_id not in announcement_targets
        ):
            raise NotificationTargetRegistryError(
                f"Notification route '{route.object_id}' references unknown "
                f"announcement target '{route.announcement_target_id}'."
            )

    return NotificationRegistry(
        notification_targets=notification_targets,
        announcement_targets=announcement_targets,
        notification_routes=notification_routes,
    )


def load_notification_targets(path: Path) -> dict[str, NotificationTarget]:
    """Compatibility wrapper returning only direct notification targets."""
    return load_notification_registry(path).notification_targets
