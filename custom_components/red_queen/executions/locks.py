"""Central transaction scope lock manager with optional FIFO waiting."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any


@dataclass(frozen=True, slots=True)
class TransactionLock:
    request_id: str
    requested_id: str
    executor: str
    scope: str
    room_id: str | None
    acquired_at: datetime

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "requested_id": self.requested_id,
            "executor": self.executor,
            "scope": self.scope,
            "room_id": self.room_id,
            "acquired_at": self.acquired_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class QueueTicket:
    request_id: str
    requested_id: str
    executor: str
    scope: str
    room_id: str | None
    queued_at: datetime
    timeout_seconds: float

    def as_dict(self, position: int | None = None) -> dict[str, Any]:
        result = {
            "request_id": self.request_id,
            "requested_id": self.requested_id,
            "executor": self.executor,
            "scope": self.scope,
            "room_id": self.room_id,
            "queued_at": self.queued_at.isoformat(),
            "timeout_seconds": self.timeout_seconds,
        }
        if position is not None:
            result["position"] = position
        return result


@dataclass(frozen=True, slots=True)
class LockDecision:
    acquired: bool
    status: str
    reason: str
    lock: TransactionLock | None
    conflict: TransactionLock | None
    queued: bool = False
    queue_wait_ms: float = 0.0
    queue_position: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "acquired": self.acquired,
            "status": self.status,
            "reason": self.reason,
            "lock": self.lock.as_dict() if self.lock else None,
            "conflict": (
                self.conflict.as_dict()
                if self.conflict
                else None
            ),
            "queued": self.queued,
            "queue_wait_ms": self.queue_wait_ms,
            "queue_position": self.queue_position,
        }


class TransactionLockManager:
    """Coordinate execution scopes and optional FIFO waiting."""

    VERSION = "1.1-stage3.7"

    def __init__(self) -> None:
        self._condition = asyncio.Condition()
        self._locks: dict[str, TransactionLock] = {}
        self._queue: deque[QueueTicket] = deque()

    @staticmethod
    def _conflicts(
        requested_scope: str,
        requested_room_id: str | None,
        active: TransactionLock,
    ) -> bool:
        if requested_scope == "house":
            return True
        if active.scope == "house":
            return True
        if requested_scope == "room":
            return active.room_id == requested_room_id
        if requested_scope == "object":
            return (
                active.scope == "room"
                and active.room_id == requested_room_id
            )
        return True

    def _find_conflict(
        self,
        scope: str,
        room_id: str | None,
    ) -> TransactionLock | None:
        for active in self._locks.values():
            if self._conflicts(scope, room_id, active):
                return active
        return None

    def _create_lock(
        self,
        *,
        request_id: str,
        requested_id: str,
        executor: str,
        scope: str,
        room_id: str | None,
    ) -> TransactionLock:
        lock = TransactionLock(
            request_id=request_id,
            requested_id=requested_id,
            executor=executor,
            scope=scope,
            room_id=room_id,
            acquired_at=datetime.now(UTC),
        )
        self._locks[request_id] = lock
        return lock

    async def async_acquire(
        self,
        *,
        request_id: str,
        requested_id: str,
        executor: str,
        scope: str,
        room_id: str | None,
        wait: bool = False,
        timeout_seconds: float = 15.0,
    ) -> LockDecision:
        """Atomically acquire, reject, or wait in strict FIFO order."""
        async with self._condition:
            conflict = self._find_conflict(scope, room_id)
            queue_busy = bool(self._queue)

            if conflict is None and not queue_busy:
                lock = self._create_lock(
                    request_id=request_id,
                    requested_id=requested_id,
                    executor=executor,
                    scope=scope,
                    room_id=room_id,
                )
                return LockDecision(
                    acquired=True,
                    status="acquired",
                    reason="Transaction lock acquired.",
                    lock=lock,
                    conflict=None,
                )

            if not wait:
                if conflict is not None and conflict.scope == "house":
                    reason = "House transaction is currently active."
                elif conflict is not None and room_id:
                    reason = (
                        f"Room {room_id!r} is currently executing "
                        "another transaction."
                    )
                elif queue_busy:
                    reason = "Transaction scheduler queue is currently busy."
                else:
                    reason = "Execution scope is currently locked."
                return LockDecision(
                    acquired=False,
                    status="locked",
                    reason=reason,
                    lock=None,
                    conflict=conflict,
                )

            ticket = QueueTicket(
                request_id=request_id,
                requested_id=requested_id,
                executor=executor,
                scope=scope,
                room_id=room_id,
                queued_at=datetime.now(UTC),
                timeout_seconds=timeout_seconds,
            )
            self._queue.append(ticket)
            initial_position = len(self._queue)
            wait_started = perf_counter()
            deadline = wait_started + timeout_seconds

            try:
                while True:
                    is_first = (
                        bool(self._queue)
                        and self._queue[0].request_id == request_id
                    )
                    conflict = self._find_conflict(scope, room_id)

                    if is_first and conflict is None:
                        self._queue.popleft()
                        lock = self._create_lock(
                            request_id=request_id,
                            requested_id=requested_id,
                            executor=executor,
                            scope=scope,
                            room_id=room_id,
                        )
                        self._condition.notify_all()
                        return LockDecision(
                            acquired=True,
                            status="acquired_after_wait",
                            reason=(
                                "Queued transaction reached the scheduler "
                                "front and acquired its lock."
                            ),
                            lock=lock,
                            conflict=None,
                            queued=True,
                            queue_wait_ms=round(
                                (perf_counter() - wait_started) * 1000,
                                2,
                            ),
                            queue_position=initial_position,
                        )

                    remaining = deadline - perf_counter()
                    if remaining <= 0:
                        self._queue = deque(
                            item
                            for item in self._queue
                            if item.request_id != request_id
                        )
                        self._condition.notify_all()
                        return LockDecision(
                            acquired=False,
                            status="queue_timeout",
                            reason=(
                                "Queued transaction did not acquire a lock "
                                "before its timeout."
                            ),
                            lock=None,
                            conflict=conflict,
                            queued=True,
                            queue_wait_ms=round(
                                (perf_counter() - wait_started) * 1000,
                                2,
                            ),
                            queue_position=initial_position,
                        )

                    try:
                        await asyncio.wait_for(
                            self._condition.wait(),
                            timeout=remaining,
                        )
                    except TimeoutError:
                        continue
            except asyncio.CancelledError:
                self._queue = deque(
                    item
                    for item in self._queue
                    if item.request_id != request_id
                )
                self._condition.notify_all()
                raise

    async def async_release(self, request_id: str) -> None:
        async with self._condition:
            self._locks.pop(request_id, None)
            self._condition.notify_all()

    async def async_snapshot(self) -> dict[str, Any]:
        async with self._condition:
            locks = sorted(
                self._locks.values(),
                key=lambda item: item.acquired_at,
            )
            queue = list(self._queue)
            return {
                "manager_version": self.VERSION,
                "active_lock_count": len(locks),
                "queue_count": len(queue),
                "house_locked": any(
                    item.scope == "house"
                    for item in locks
                ),
                "room_locks": sorted({
                    item.room_id
                    for item in locks
                    if item.room_id is not None
                }),
                "locks": [item.as_dict() for item in locks],
                "queue": [
                    item.as_dict(position=index)
                    for index, item in enumerate(queue, start=1)
                ],
            }
