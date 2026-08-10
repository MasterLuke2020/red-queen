"""Home Assistant-safe asynchronous file helpers for WNHF."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Callable, TypeVar

from homeassistant.core import HomeAssistant

_T = TypeVar("_T")


class AsyncFileHelper:
    """Execute blocking filesystem operations outside the HA event loop."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def run(
        self,
        func: Callable[..., _T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> _T:
        """Run one blocking filesystem callable in Home Assistant's executor."""
        if kwargs:
            return await self._hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )
        return await self._hass.async_add_executor_job(func, *args)

    async def exists(self, path: Path) -> bool:
        return await self.run(path.exists)

    async def read_text(
        self,
        path: Path,
        *,
        encoding: str = "utf-8",
    ) -> str:
        return await self.run(path.read_text, encoding=encoding)

    async def mkdir(
        self,
        path: Path,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        await self.run(
            path.mkdir,
            parents=parents,
            exist_ok=exist_ok,
        )
