"""Native semantic notification routing and announcement provider."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
from math import ceil
import re
from typing import Any
from urllib.parse import urlencode

from ..const import NOTIFICATION_TARGETS_FILE
from ..domain.capability import CapabilitySnapshot, CapabilityState
from ..domain.notification import (
    ANNOUNCEMENT_LEVELS,
    NOTIFICATION_PRIORITIES,
    NOTIFICATION_PROFILES,
    AnnouncementTarget,
    NotificationRegistry,
    NotificationRoute,
    NotificationTarget,
    load_notification_registry,
)
from .base import ProviderKind, WNHFProvider
from .execution import ProviderExecutionResult, ProviderExecutionValidationResult


_LOGGER = logging.getLogger(__name__)


class NotificationCapabilityProvider(WNHFProvider):
    """Provider-neutral native notification and announcement runtime."""

    provider_name = "NotificationCapabilityProvider"
    provider_kind = ProviderKind.CORE
    provider_version = "2.1.0"
    discoverable = True
    priority = 100

    _ACTION_SEND = "notifications.send"
    _ACTION_ANNOUNCE = "notifications.announce"
    _ACTION_ROUTE = "notifications.route"

    def __init__(self, engine) -> None:
        super().__init__(engine.hass)
        self.engine = engine
        self._registry = NotificationRegistry({}, {}, {})
        self._load_error: str | None = None
        self._last_reload_at: str | None = None
        self._last_dispatch_at: dict[str, str] = {}
        self._last_announcement_at: dict[str, str] = {}
        self._last_route_at: dict[str, str] = {}
        self._last_route_result: dict[str, Any] | None = None
        self._announcement_locks: dict[str, asyncio.Lock] = {}

    @property
    def provider_id(self) -> str:
        return "provider.core.notifications"

    @property
    def _registry_path(self):
        return self.engine.registry_dir / NOTIFICATION_TARGETS_FILE

    @property
    def _targets(self) -> dict[str, NotificationTarget]:
        return self._registry.notification_targets

    @property
    def _announcement_targets(self) -> dict[str, AnnouncementTarget]:
        return self._registry.announcement_targets

    @property
    def _routes(self) -> dict[str, NotificationRoute]:
        return self._registry.notification_routes

    def supported_capabilities(self) -> tuple[str, ...]:
        return ("notifications",)

    async def async_setup(self) -> None:
        await super().async_setup()
        await self._async_reload_registry()

    async def _async_reload_registry(self) -> None:
        try:
            registry = await self.hass.async_add_executor_job(
                load_notification_registry, self._registry_path
            )
        except Exception as err:  # noqa: BLE001
            self._registry = NotificationRegistry({}, {}, {})
            self._load_error = f"{type(err).__name__}: {err}"
        else:
            self._registry = registry
            self._load_error = None
        self._last_reload_at = datetime.now(UTC).isoformat()

    def _service_available(self, domain: str, service: str) -> bool:
        return self.hass.services.has_service(domain, service)

    def _entity_available(self, entity_id: str) -> bool:
        state = self.hass.states.get(entity_id)
        return state is not None and state.state not in {
            "unavailable",
            "unknown",
        }

    def _tts_entity_available(self, entity_id: str) -> bool:
        state = self.hass.states.get(entity_id)
        # TTS entities can legitimately expose ``unknown`` before their first
        # synthesis. Only absence or explicit unavailability blocks dispatch.
        return state is not None and state.state != "unavailable"

    def _notification_target_available(self, target: NotificationTarget) -> bool:
        return (
            target.enabled
            and self._service_available("notify", "send_message")
            and self._entity_available(target.entity_id)
        )

    def _announcement_target_available(
        self, target: AnnouncementTarget, level: str | None = None
    ) -> bool:
        if not target.enabled:
            return False
        if not self._tts_entity_available(target.tts_entity_id):
            return False
        if target.provider == "home_assistant_tts_sonos":
            if not self._service_available("media_player", "play_media"):
                return False
        elif (
            not self._service_available("tts", "speak")
            or not self._service_available("media_player", "volume_set")
        ):
            return False
        profiles = (
            (target.levels[level],)
            if level is not None
            else tuple(target.levels.values())
        )
        return any(
            all(
                self._entity_available(entity_id)
                for entity_id in profile.speaker_entity_ids
            )
            for profile in profiles
        )

    def _route_available(self, route: NotificationRoute) -> bool:
        if not route.enabled:
            return False
        mobile = any(
            self._notification_target_available(self._targets[target_id])
            for target_id in route.notification_target_ids
        )
        voice = (
            route.announcement_target_id is not None
            and self._announcement_target_available(
                self._announcement_targets[route.announcement_target_id]
            )
        )
        dashboard = route.dashboard_enabled and self._service_available(
            "persistent_notification", "create"
        )
        return route.log_enabled or mobile or voice or dashboard

    def _technical_send(self, target: NotificationTarget) -> dict[str, Any]:
        return {
            "capability_id": "notifications",
            "action_id": self._ACTION_SEND,
            "target_id": target.object_id,
            "provider": target.provider,
            "entity_id": target.entity_id,
            "service": "notify.send_message",
            "available": self._notification_target_available(target),
            "verification_scope": "dispatch",
            "delivery_receipt_claimed": False,
            "read_receipt_claimed": False,
        }

    def _technical_announcement(
        self, target: AnnouncementTarget, level: str
    ) -> dict[str, Any]:
        profile = target.levels[level]
        native_sonos_announce = (
            target.provider == "home_assistant_tts_sonos"
        )
        return {
            "capability_id": "notifications",
            "action_id": self._ACTION_ANNOUNCE,
            "target_id": target.object_id,
            "provider": target.provider,
            "tts_entity_id": target.tts_entity_id,
            "speaker_entity_ids": list(profile.speaker_entity_ids),
            "level": level,
            "service": (
                "media_player.play_media"
                if native_sonos_announce
                else "tts.speak"
            ),
            "native_sonos_announce": native_sonos_announce,
            "snapshot_restore": False,
            "available": self._announcement_target_available(target, level),
            "verification_scope": "dispatch",
            "playback_heard_claimed": False,
        }

    def _technical_route(
        self, route: NotificationRoute, *, profile: str, priority: str
    ) -> dict[str, Any]:
        plan = self._route_plan(route, profile=profile)
        return {
            "capability_id": "notifications",
            "action_id": self._ACTION_ROUTE,
            "target_id": route.object_id,
            "priority": priority,
            "profile": profile,
            "selected_channels": plan["selected_channels"],
            "voice_context": plan["voice_context"],
            "available": self._route_available(route),
            "verification_scope": "dispatch",
            "delivery_receipt_claimed": False,
            "read_receipt_claimed": False,
            "playback_heard_claimed": False,
        }

    def snapshot(self) -> CapabilitySnapshot:
        direct_enabled = [t for t in self._targets.values() if t.enabled]
        announcement_enabled = [
            t for t in self._announcement_targets.values() if t.enabled
        ]
        route_enabled = [t for t in self._routes.values() if t.enabled]
        direct_available = [
            t for t in direct_enabled if self._notification_target_available(t)
        ]
        announcement_available = [
            t
            for t in announcement_enabled
            if self._announcement_target_available(t)
        ]
        route_available = [
            t for t in route_enabled if self._route_available(t)
        ]
        configured = (
            len(self._targets)
            + len(self._announcement_targets)
            + len(self._routes)
        )
        supported = configured > 0
        available = (
            supported
            and self._load_error is None
            and bool(
                direct_available
                or announcement_available
                or route_available
            )
        )
        healthy = available

        if not supported:
            state = CapabilityState.UNSUPPORTED
            message = (
                "Notifications are not configured."
                if self._load_error is None
                else "Notification registry is invalid."
            )
        elif not available:
            state = CapabilityState.UNAVAILABLE
            message = (
                "Notification objects are configured but no enabled target "
                "is currently dispatchable."
            )
        else:
            state = CapabilityState.HEALTHY
            message = "Native notification routing and announcements available."

        targets = [
            {
                **target.as_dict(),
                "available": self._notification_target_available(target),
                "last_dispatch_at": self._last_dispatch_at.get(target.object_id),
            }
            for target in sorted(
                self._targets.values(), key=lambda item: item.object_id
            )
        ]
        announcement_targets = [
            {
                **target.as_dict(),
                "available": self._announcement_target_available(target),
                "last_announcement_at": self._last_announcement_at.get(
                    target.object_id
                ),
            }
            for target in sorted(
                self._announcement_targets.values(),
                key=lambda item: item.object_id,
            )
        ]
        routes = [
            {
                **route.as_dict(),
                "available": self._route_available(route),
                "last_route_at": self._last_route_at.get(route.object_id),
            }
            for route in sorted(
                self._routes.values(), key=lambda item: item.object_id
            )
        ]
        return CapabilitySnapshot(
            capability_id="notifications",
            provider_id=self.provider_id if supported else None,
            supported=supported,
            available=available,
            healthy=healthy,
            state=state,
            message=message,
            details={
                "registry_file": str(self._registry_path),
                "load_error": self._load_error,
                "last_reload_at": self._last_reload_at,
                "notify_send_message_available": self._service_available(
                    "notify", "send_message"
                ),
                "tts_speak_available": self._service_available("tts", "speak"),
                "media_player_play_media_available": self._service_available(
                    "media_player", "play_media"
                ),
                "configured_notification_targets": len(self._targets),
                "available_notification_targets": len(direct_available),
                "configured_announcement_targets": len(
                    self._announcement_targets
                ),
                "available_announcement_targets": len(announcement_available),
                "configured_notification_routes": len(self._routes),
                "available_notification_routes": len(route_available),
                "targets": targets,
                "announcement_targets": announcement_targets,
                "notification_routes": routes,
                "canonical_actions": [
                    self._ACTION_SEND,
                    self._ACTION_ANNOUNCE,
                    self._ACTION_ROUTE,
                ],
                "announcement_levels": list(ANNOUNCEMENT_LEVELS),
                "routing_priorities": list(NOTIFICATION_PRIORITIES),
                "routing_profiles": list(NOTIFICATION_PROFILES),
                "last_route_result": self._last_route_result,
                "verification_scope": "dispatch",
                "delivery_receipt_claimed": False,
                "read_receipt_claimed": False,
                "playback_heard_claimed": False,
            },
        )

    @staticmethod
    def _message(parameters: dict[str, Any]) -> str | None:
        value = parameters.get("message")
        if not isinstance(value, str) or not value.strip():
            return None
        return value.strip()

    async def async_validate_execution(
        self,
        *,
        action_id: str,
        target: dict[str, Any],
        parameters: dict[str, Any],
        confirmed: bool,
    ) -> ProviderExecutionValidationResult:
        if action_id not in {
            self._ACTION_SEND,
            self._ACTION_ANNOUNCE,
            self._ACTION_ROUTE,
        }:
            return await super().async_validate_execution(
                action_id=action_id,
                target=target,
                parameters=parameters,
                confirmed=confirmed,
            )

        await self._async_reload_registry()
        object_id = target.get("object_id")
        if not isinstance(object_id, str) or not object_id.strip():
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"{action_id} requires target.object_id.",
                errors=("target.object_id is required.",),
            )
        if self._message(parameters) is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"{action_id} requires a non-empty message.",
                errors=("parameters.message must be a non-empty string.",),
            )

        if action_id == self._ACTION_SEND:
            return self._validate_send(str(object_id), parameters)
        if action_id == self._ACTION_ANNOUNCE:
            return self._validate_announcement(str(object_id), parameters)
        return self._validate_route(str(object_id), parameters)

    def _validate_send(
        self, object_id: str, parameters: dict[str, Any]
    ) -> ProviderExecutionValidationResult:
        title = parameters.get("title")
        if title is not None and not isinstance(title, str):
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.send title must be a string or null.",
                errors=("parameters.title must be a string or null.",),
            )
        semantic_target = self._targets.get(object_id)
        if semantic_target is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Unknown semantic notification target: {object_id}.",
                errors=(f"Unknown semantic notification target: {object_id}.",),
            )
        technical = self._technical_send(semantic_target)
        if not semantic_target.enabled:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Notification target {object_id} is disabled.",
                errors=(f"Notification target {object_id} is disabled.",),
                technical_capability=technical,
            )
        if not self._notification_target_available(semantic_target):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Notification target {object_id} is unavailable.",
                errors=(f"{semantic_target.entity_id} is unavailable.",),
                technical_capability=technical,
            )
        return ProviderExecutionValidationResult(
            valid=True,
            reason="Semantic notification target is valid for dispatch.",
            technical_capability=technical,
        )

    def _validate_announcement(
        self, object_id: str, parameters: dict[str, Any]
    ) -> ProviderExecutionValidationResult:
        level = parameters.get("level", "info")
        if not isinstance(level, str) or level not in ANNOUNCEMENT_LEVELS:
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.announce level is unsupported.",
                errors=(
                    "parameters.level must be one of: "
                    + ", ".join(ANNOUNCEMENT_LEVELS)
                    + ".",
                ),
            )
        semantic_target = self._announcement_targets.get(object_id)
        if semantic_target is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Unknown semantic announcement target: {object_id}.",
                errors=(f"Unknown semantic announcement target: {object_id}.",),
            )
        technical = self._technical_announcement(semantic_target, level)
        if not semantic_target.enabled:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Announcement target {object_id} is disabled.",
                errors=(f"Announcement target {object_id} is disabled.",),
                technical_capability=technical,
            )
        if not self._announcement_target_available(semantic_target, level):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Announcement target {object_id} is unavailable.",
                errors=(
                    "TTS, speaker or snapshot/restore dependency is unavailable.",
                ),
                technical_capability=technical,
            )
        return ProviderExecutionValidationResult(
            valid=True,
            reason="Semantic announcement target and playback profile are valid.",
            technical_capability=technical,
        )

    def _validate_route(
        self, object_id: str, parameters: dict[str, Any]
    ) -> ProviderExecutionValidationResult:
        title = parameters.get("title")
        priority = parameters.get("priority", "info")
        profile = parameters.get("profile", "standard")
        source = parameters.get("source", "unknown")
        category = parameters.get("category", "general")
        if title is not None and not isinstance(title, str):
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.route title must be a string or null.",
                errors=("parameters.title must be a string or null.",),
            )
        if not isinstance(priority, str) or priority not in NOTIFICATION_PRIORITIES:
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.route priority is unsupported.",
                errors=(
                    "parameters.priority must be one of: "
                    + ", ".join(NOTIFICATION_PRIORITIES)
                    + ".",
                ),
            )
        if not isinstance(profile, str) or profile not in NOTIFICATION_PROFILES:
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.route profile is unsupported.",
                errors=(
                    "parameters.profile must be one of: "
                    + ", ".join(NOTIFICATION_PROFILES)
                    + ".",
                ),
            )
        for key, value in (("source", source), ("category", category)):
            if not isinstance(value, str) or not value.strip():
                return ProviderExecutionValidationResult(
                    valid=False,
                    reason=f"notifications.route {key} must be non-empty.",
                    errors=(f"parameters.{key} must be a non-empty string.",),
                )
        route = self._routes.get(object_id)
        if route is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Unknown semantic notification route: {object_id}.",
                errors=(f"Unknown semantic notification route: {object_id}.",),
            )
        technical = self._technical_route(
            route, profile=profile, priority=priority
        )
        if not route.enabled:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Notification route {object_id} is disabled.",
                errors=(f"Notification route {object_id} is disabled.",),
                technical_capability=technical,
            )
        if not self._route_available(route):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Notification route {object_id} has no available channel.",
                errors=("No configured route channel is currently available.",),
                technical_capability=technical,
            )
        if not technical["selected_channels"]:
            return ProviderExecutionValidationResult(
                valid=False,
                reason="Notification profile selected no route channel.",
                errors=("No notification channel selected.",),
                technical_capability=technical,
            )
        return ProviderExecutionValidationResult(
            valid=True,
            reason="Semantic notification route and channel policy are valid.",
            technical_capability=technical,
        )

    async def async_execute(
        self,
        *,
        action_id: str,
        target: dict[str, Any],
        parameters: dict[str, Any],
        confirmed: bool,
    ) -> ProviderExecutionResult:
        if action_id not in {
            self._ACTION_SEND,
            self._ACTION_ANNOUNCE,
            self._ACTION_ROUTE,
        }:
            return await super().async_execute(
                action_id=action_id,
                target=target,
                parameters=parameters,
                confirmed=confirmed,
            )

        validation = await self.async_validate_execution(
            action_id=action_id,
            target=target,
            parameters=parameters,
            confirmed=confirmed,
        )
        if not validation.valid:
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=validation.reason,
                technical_capability=validation.technical_capability,
                verification_scope="dispatch",
            )

        object_id = str(target["object_id"])
        if action_id == self._ACTION_SEND:
            return await self._execute_send(
                object_id, parameters, validation.technical_capability
            )
        if action_id == self._ACTION_ANNOUNCE:
            return await self._execute_announcement(
                object_id, parameters, validation.technical_capability
            )
        return await self._execute_route(
            object_id, parameters, validation.technical_capability
        )

    async def _execute_send(
        self,
        object_id: str,
        parameters: dict[str, Any],
        technical: dict[str, Any] | None,
    ) -> ProviderExecutionResult:
        target = self._targets[object_id]
        try:
            await self._dispatch_notification_target(target, parameters)
        except Exception as err:  # noqa: BLE001
            return ProviderExecutionResult(
                status="failed",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason="Home Assistant notification dispatch failed.",
                error=f"{type(err).__name__}: {err}",
                technical_capability=technical,
                verification_scope="dispatch",
            )
        dispatched_at = datetime.now(UTC).isoformat()
        self._last_dispatch_at[object_id] = dispatched_at
        return ProviderExecutionResult(
            status="succeeded",
            executed=True,
            command_sent=True,
            feedback_confirmed=True,
            reason=(
                "Notification dispatch was accepted by the Home Assistant "
                "notify entity. Delivery/read receipt is not claimed."
            ),
            technical_capability=technical,
            feedback_after={
                "target_id": object_id,
                "entity_id": target.entity_id,
                "dispatched_at": dispatched_at,
                "verification_scope": "dispatch",
                "delivery_receipt_claimed": False,
                "read_receipt_claimed": False,
            },
            verification_scope="dispatch",
        )

    async def _dispatch_notification_target(
        self, target: NotificationTarget, parameters: dict[str, Any]
    ) -> None:
        service_data: dict[str, Any] = {
            "entity_id": target.entity_id,
            "message": str(parameters["message"]).strip(),
        }
        title = parameters.get("title")
        if isinstance(title, str) and title.strip():
            service_data["title"] = title.strip()
        await self.hass.services.async_call(
            "notify", "send_message", service_data, blocking=True
        )

    async def _execute_announcement(
        self,
        object_id: str,
        parameters: dict[str, Any],
        technical: dict[str, Any] | None,
    ) -> ProviderExecutionResult:
        target = self._announcement_targets[object_id]
        level = str(parameters.get("level", "info"))
        message = str(parameters["message"]).strip()
        try:
            result = await self._perform_announcement(
                target=target,
                message=message,
                level=level,
            )
        except Exception as err:  # noqa: BLE001
            return ProviderExecutionResult(
                status="failed",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason="Native Home Assistant announcement failed.",
                error=f"{type(err).__name__}: {err}",
                technical_capability=technical,
                verification_scope="dispatch",
            )
        self._last_announcement_at[object_id] = result["dispatched_at"]
        native_sonos_announce = result["restore_strategy"] == (
            "sonos_native_announce"
        )
        return ProviderExecutionResult(
            status="succeeded",
            executed=True,
            command_sent=True,
            feedback_confirmed=True,
            reason=(
                "Sonos native announcement dispatch was accepted; Sonos owns "
                "overlay restoration. Audible playback and restoration "
                "completion are not claimed."
                if native_sonos_announce
                else "TTS dispatch and configured volume restoration completed. "
                "Audible playback is not claimed."
            ),
            technical_capability=technical,
            feedback_after=result,
            feedback_wait_ms=(
                0.0
                if native_sonos_announce
                else float(result["duration_seconds"]) * 1000
            ),
            verification_scope="dispatch",
        )

    async def _perform_announcement(
        self,
        *,
        target: AnnouncementTarget,
        message: str,
        level: str,
    ) -> dict[str, Any]:
        profile = target.levels[level]
        speakers = list(profile.speaker_entity_ids)
        spoken_message = (
            f"{profile.prefix} {message}" if profile.prefix else message
        )
        duration_seconds = min(
            target.maximum_seconds,
            max(
                target.minimum_seconds,
                ceil(
                    len(spoken_message.split()) * target.seconds_per_word
                    + target.padding_seconds
                ),
            ),
        )
        lock = self._announcement_locks.setdefault(
            target.object_id, asyncio.Lock()
        )
        async with lock:
            if target.provider == "home_assistant_tts_sonos":
                query = urlencode({"message": spoken_message})
                await self.hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": (
                            speakers[0] if len(speakers) == 1 else speakers
                        ),
                        "announce": True,
                        "media_content_type": "music",
                        "media_content_id": (
                            f"media-source://tts/{target.tts_entity_id}?{query}"
                        ),
                        "extra": {
                            "volume": round(profile.volume * 100),
                        },
                    },
                    blocking=True,
                )
                # Keep the semantic target lock for the estimated announcement
                # window so a second Red Queen request cannot overlap it. No
                # restore command is sent after this wait; Sonos owns playback
                # ducking and restoration through the native announce overlay.
                await asyncio.sleep(duration_seconds)
                return {
                    "target_id": target.object_id,
                    "level": level,
                    "tts_entity_id": target.tts_entity_id,
                    "speaker_entity_ids": speakers,
                    "duration_seconds": duration_seconds,
                    "restore_strategy": "sonos_native_announce",
                    "restore_completed_by_framework": False,
                    "dispatched_at": datetime.now(UTC).isoformat(),
                    "verification_scope": "dispatch",
                    "playback_heard_claimed": False,
                }

            original_volumes: dict[str, float] = {}
            restored = False
            primary_error: Exception | None = None
            try:
                for entity_id in speakers:
                    state = self.hass.states.get(entity_id)
                    volume = (
                        state.attributes.get("volume_level")
                        if state is not None
                        else None
                    )
                    if isinstance(volume, (int, float)):
                        original_volumes[entity_id] = float(volume)

                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {
                        "entity_id": speakers,
                        "volume_level": profile.volume,
                    },
                    blocking=True,
                )
                await self.hass.services.async_call(
                    "tts",
                    "speak",
                    {
                        "entity_id": target.tts_entity_id,
                        "media_player_entity_id": (
                            speakers[0] if len(speakers) == 1 else speakers
                        ),
                        "message": spoken_message,
                        "cache": target.cache,
                    },
                    blocking=True,
                )
                await asyncio.sleep(duration_seconds)
            except Exception as err:  # noqa: BLE001
                primary_error = err
            finally:
                try:
                    for entity_id, volume in original_volumes.items():
                        await self.hass.services.async_call(
                            "media_player",
                            "volume_set",
                            {
                                "entity_id": entity_id,
                                "volume_level": volume,
                            },
                            blocking=True,
                        )
                    if original_volumes:
                        restored = True
                except Exception as restore_error:  # noqa: BLE001
                    if primary_error is None:
                        primary_error = restore_error
                    else:
                        _LOGGER.exception(
                            "Announcement restore failed after dispatch error",
                            exc_info=restore_error,
                        )
            if primary_error is not None:
                raise primary_error

        return {
            "target_id": target.object_id,
            "level": level,
            "tts_entity_id": target.tts_entity_id,
            "speaker_entity_ids": speakers,
            "duration_seconds": duration_seconds,
            "restore_strategy": "framework_volume_restore",
            "restore_completed_by_framework": restored,
            "dispatched_at": datetime.now(UTC).isoformat(),
            "verification_scope": "dispatch",
            "playback_heard_claimed": False,
        }

    def _route_plan(
        self, route: NotificationRoute, *, profile: str
    ) -> dict[str, Any]:
        house_state: str | None = None
        if route.house_state_entity_id is not None:
            state = self.hass.states.get(route.house_state_entity_id)
            house_state = (
                str(state.state).lower().strip()
                if state is not None
                else "unknown"
            )
        quiet_mode = False
        if route.quiet_mode_entity_id is not None:
            state = self.hass.states.get(route.quiet_mode_entity_id)
            quiet_mode = state is not None and state.state == "on"

        voice_context_allowed = (
            not quiet_mode
            and (
                house_state is None
                or house_state not in route.voice_blocked_states
            )
        )
        dashboard = route.dashboard_enabled and profile in {
            "standard",
            "silent",
            "voice",
            "broadcast",
        }
        mobile = profile in {
            "standard",
            "silent",
            "mobile",
            "broadcast",
        }
        if profile == "broadcast":
            voice = True
            suppression_reason = None
        elif profile in {"standard", "voice"}:
            voice = voice_context_allowed
            suppression_reason = (
                None if voice else "quiet_mode_or_house_state"
            )
        else:
            voice = False
            suppression_reason = "profile"

        selected_channels = []
        if route.log_enabled:
            selected_channels.append("log")
        if dashboard:
            selected_channels.append("dashboard")
        if mobile:
            selected_channels.append("mobile")
        if voice:
            selected_channels.append("voice")
        return {
            "selected_channels": selected_channels,
            "log": route.log_enabled,
            "dashboard": dashboard,
            "mobile": mobile,
            "voice": voice,
            "voice_context": {
                "quiet_mode": quiet_mode,
                "house_state": house_state,
                "allowed": voice_context_allowed,
                "suppression_reason": suppression_reason,
                "broadcast_override": profile == "broadcast",
            },
        }

    @staticmethod
    def _announcement_level(priority: str) -> str:
        return {
            "critical": "alarm",
            "warning": "warning",
            "debug": "notice",
            "info": "info",
        }[priority]

    async def _execute_route(
        self,
        object_id: str,
        parameters: dict[str, Any],
        technical: dict[str, Any] | None,
    ) -> ProviderExecutionResult:
        route = self._routes[object_id]
        message = str(parameters["message"]).strip()
        title = parameters.get("title")
        title = title.strip() if isinstance(title, str) and title.strip() else "Red Queen"
        priority = str(parameters.get("priority", "info"))
        profile = str(parameters.get("profile", "standard"))
        source = str(parameters.get("source", "unknown")).strip()
        category = str(parameters.get("category", "general")).strip().lower()
        plan = self._route_plan(route, profile=profile)
        channel_results: list[dict[str, Any]] = []

        if plan["log"]:
            channel_results.append(
                await self._route_log(
                    title=title,
                    message=message,
                    priority=priority,
                    profile=profile,
                    source=source,
                    category=category,
                    context=plan["voice_context"],
                    entity_id=route.house_state_entity_id,
                )
            )
        if plan["dashboard"]:
            channel_results.append(
                await self._route_dashboard(
                    title=title,
                    message=message,
                    priority=priority,
                    profile=profile,
                    source=source,
                    category=category,
                )
            )
        if plan["mobile"]:
            if not route.notification_target_ids:
                channel_results.append(
                    {
                        "channel": "mobile",
                        "target_id": None,
                        "status": "unconfigured",
                    }
                )
            for target_id in route.notification_target_ids:
                target = self._targets[target_id]
                if not self._notification_target_available(target):
                    channel_results.append(
                        {
                            "channel": "mobile",
                            "target_id": target_id,
                            "status": "unavailable",
                        }
                    )
                    continue
                try:
                    await self._dispatch_notification_target(
                        target,
                        {"message": message, "title": title},
                    )
                except Exception as err:  # noqa: BLE001
                    channel_results.append(
                        {
                            "channel": "mobile",
                            "target_id": target_id,
                            "status": "failed",
                            "error": f"{type(err).__name__}: {err}",
                        }
                    )
                else:
                    dispatched_at = datetime.now(UTC).isoformat()
                    self._last_dispatch_at[target_id] = dispatched_at
                    channel_results.append(
                        {
                            "channel": "mobile",
                            "target_id": target_id,
                            "status": "succeeded",
                            "dispatched_at": dispatched_at,
                        }
                    )
        if plan["voice"]:
            target_id = route.announcement_target_id
            if target_id is None:
                channel_results.append(
                    {
                        "channel": "voice",
                        "target_id": None,
                        "status": "unconfigured",
                    }
                )
            else:
                target = self._announcement_targets[target_id]
                announcement_level = self._announcement_level(priority)
                if not self._announcement_target_available(
                    target, announcement_level
                ):
                    channel_results.append(
                        {
                            "channel": "voice",
                            "target_id": target_id,
                            "status": "unavailable",
                        }
                    )
                else:
                    try:
                        voice_result = await self._perform_announcement(
                            target=target,
                            message=message,
                            level=announcement_level,
                        )
                    except Exception as err:  # noqa: BLE001
                        channel_results.append(
                            {
                                "channel": "voice",
                                "target_id": target_id,
                                "status": "failed",
                                "error": f"{type(err).__name__}: {err}",
                            }
                        )
                    else:
                        self._last_announcement_at[target_id] = voice_result[
                            "dispatched_at"
                        ]
                        channel_results.append(
                            {
                                "channel": "voice",
                                "target_id": target_id,
                                "status": "succeeded",
                                "result": voice_result,
                            }
                        )

        selected_external = {
            "dashboard",
            "mobile",
            "voice",
        }.intersection(plan["selected_channels"])
        if not selected_external and not plan["log"]:
            channel_results.append(
                {"channel": "none", "status": "skipped"}
            )

        succeeded = [
            item for item in channel_results if item["status"] == "succeeded"
        ]
        failed = [
            item
            for item in channel_results
            if item["status"] in {"failed", "unavailable", "unconfigured"}
        ]
        routed_at = datetime.now(UTC).isoformat()
        feedback = {
            "route_id": object_id,
            "priority": priority,
            "profile": profile,
            "source": source,
            "category": category,
            "selected_channels": plan["selected_channels"],
            "voice_context": plan["voice_context"],
            "channel_results": channel_results,
            "routed_at": routed_at,
            "verification_scope": "dispatch",
            "delivery_receipt_claimed": False,
            "read_receipt_claimed": False,
            "playback_heard_claimed": False,
        }
        self._last_route_at[object_id] = routed_at
        self._last_route_result = feedback
        if failed:
            return ProviderExecutionResult(
                status="failed",
                executed=bool(succeeded),
                command_sent=bool(succeeded),
                feedback_confirmed=False,
                reason="Notification route completed with channel failures.",
                error="One or more selected notification channels failed.",
                technical_capability=technical,
                feedback_after=feedback,
                verification_scope="dispatch",
            )
        return ProviderExecutionResult(
            status="succeeded",
            executed=bool(succeeded),
            command_sent=bool(succeeded),
            feedback_confirmed=bool(succeeded),
            reason=(
                "Native notification routing completed for every selected "
                "available channel. Delivery/read/heard state is not claimed."
            ),
            technical_capability=technical,
            feedback_after=feedback,
            verification_scope="dispatch",
        )

    async def _route_log(
        self,
        *,
        title: str,
        message: str,
        priority: str,
        profile: str,
        source: str,
        category: str,
        context: dict[str, Any],
        entity_id: str | None,
    ) -> dict[str, Any]:
        rendered = (
            f"[{priority.upper()}] {message} · Profile: {profile} · "
            f"Source: {source} · Category: {category} · "
            f"House State: {context['house_state']} · "
            f"Quiet Mode: {context['quiet_mode']}"
        )
        try:
            if self._service_available("logbook", "log"):
                service_data = {
                    "name": f"Red Queen · {title}",
                    "message": rendered,
                }
                if entity_id is not None:
                    service_data["entity_id"] = entity_id
                await self.hass.services.async_call(
                    "logbook",
                    "log",
                    service_data,
                    blocking=True,
                )
            else:
                _LOGGER.info("%s", rendered)
        except Exception as err:  # noqa: BLE001
            return {
                "channel": "log",
                "status": "failed",
                "error": f"{type(err).__name__}: {err}",
            }
        return {"channel": "log", "status": "succeeded"}

    async def _route_dashboard(
        self,
        *,
        title: str,
        message: str,
        priority: str,
        profile: str,
        source: str,
        category: str,
    ) -> dict[str, Any]:
        if priority not in {"warning", "critical"}:
            return {
                "channel": "dashboard",
                "status": "skipped_priority",
            }
        if not self._service_available("persistent_notification", "create"):
            return {"channel": "dashboard", "status": "unavailable"}
        notification_id = self._notification_id(source, category)
        title_prefix = "🚨" if priority == "critical" else "⚠️"
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": f"{title_prefix} {title}",
                    "message": (
                        f"{message}\n\nPriority: {priority}  \n"
                        f"Profile: {profile}  \nSource: {source}  \n"
                        f"Category: {category}"
                    ),
                    "notification_id": notification_id,
                },
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001
            return {
                "channel": "dashboard",
                "status": "failed",
                "error": f"{type(err).__name__}: {err}",
            }
        return {
            "channel": "dashboard",
            "status": "succeeded",
            "notification_id": notification_id,
        }

    @staticmethod
    def _notification_id(source: str, category: str) -> str:
        raw = f"wnhf_notify_{source}_{category}".lower()
        normalized = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
        return normalized or "wnhf_notify_general"
