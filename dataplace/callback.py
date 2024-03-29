# callback.py

from typing import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
import asyncio

from dataplace.io import ModelIO

__all__ = [
    "Callback"
]

Data = ModelIO | object

@dataclass
class Callback:

    callback: Callable[[Data], Awaitable[...] | ...] = None
    preparation: Callable[[], Awaitable[...] | ...] = None
    types: Iterable[type[Data]] = field(default_factory=set)
    enabled: bool = True
    prepared: bool = False

    async def async_prepare(self) -> None:
        """Connects to the socket service."""

        if self.preparation:
            if asyncio.iscoroutinefunction(self.preparation):
                await self.preparation()

            else:
                self.preparation()

        self.prepared = True

    def prepare(self) -> None:
        """Connects to the socket service."""

        if self.preparation:
            if asyncio.iscoroutinefunction(self.preparation):
                asyncio.run(self.preparation())

            else:
                self.preparation()

        self.prepared = True

    async def async_execute(self, data: Data) -> None:

        if not isinstance(data, tuple(self.types)):
            return

        if self.enabled:
            if not self.prepared:
                await self.async_prepare()

            await self.async_call(data=data)

    def execute(self, data: Data) -> None:

        if not isinstance(data, tuple(self.types)):
            return

        if self.enabled:
            if not self.prepared:
                self.prepare()

            self.call(data=data)

    async def async_call(self, data: Data) -> None:

        if self.callback is not None:
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(data)

            else:
                self.callback(data)

    def call(self, data: Data) -> None:

        if self.callback is not None:
            if asyncio.iscoroutinefunction(self.callback):
                asyncio.run(self.callback(data))

            else:
                self.callback(data)

    def enable(self) -> None:

        self.enabled = True

    def disable(self) -> None:

        self.enabled = False
