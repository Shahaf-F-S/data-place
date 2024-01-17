# callback.py

from typing import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
import asyncio

from socketos.io import ModelIO

__all__ = [
    "Callback"
]

_TYPES = lambda: {ModelIO}

@dataclass
class Callback:

    types: Iterable[type[ModelIO]] = field(default_factory=_TYPES)
    callback: Callable[[ModelIO], Awaitable[...] | ...] = None
    preparation: Callable[[], Awaitable[...] | ...] = None
    enabled: bool = True
    prepared: bool = False

    async def prepare(self) -> None:
        """Connects to the socket service."""

        if self.preparation:
            if asyncio.iscoroutinefunction(self.preparation):
                await self.preparation()

            else:
                self.preparation()

        self.prepared = True

    async def execute(self, data: ModelIO) -> None:

        if not isinstance(data, tuple(self.types)):
            return

        if self.enabled:
            if not self.prepared:
                await self.prepare()

            await self.call(data=data)

    async def call(self, data: ModelIO) -> None:

        if self.callback is not None:
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(data)

            else:
                self.callback(data)

    def enable(self) -> None:

        self.enabled = True

    def disable(self) -> None:

        self.enabled = False
