# control.py

import time
from dataclasses import dataclass, field
import asyncio
from typing import Callable, Awaitable, Iterable

from dataplace.io import ModelIO
from dataplace.callback import Callback
from dataplace.handler import Handler

__all__ = [
    "Controller",
    "loop",
    "async_loop"
]

Data = ModelIO | object

@dataclass
class Controller:

    callbacks: list[Callback] = field(default_factory=list)
    controllers: list["Controller"] = field(default_factory=list)
    handler: Handler = field(default_factory=Handler)
    paused: bool = False
    running: bool = True
    enabled: bool = True
    delay: float = 0.00001
    data: ... = None

    def pause(self) -> None:

        self.paused = True

        for controller in self.controllers:
            controller.pause()

    def unpause(self) -> None:

        self.paused = False

        for controller in self.controllers:
            controller.unpause()

    def stop(self) -> None:

        self.paused = False
        self.running = False

        for controller in self.controllers:
            controller.stop()

    def run(self) -> None:

        self.running = True

        for controller in self.controllers:
            controller.run()

    def enable(self) -> None:

        self.enabled = True

        for controller in self.controllers:
            controller.enable()

    def disable(self) -> None:

        self.enabled = False

        for controller in self.controllers:
            controller.disable()

    async def async_callback(self, data: Data) -> None:

        if self.callbacks:
            with self.handler:
                await asyncio.gather(
                    *(
                        callback.async_execute(data)
                        for callback in self.callbacks
                    )
                )

    def callback(self, data: Data) -> None:

        if self.callbacks:
            with self.handler:
                for callback in self.callbacks:
                    callback.execute(data)

    async def async_hold(self) -> None:

        while self.paused:
            await asyncio.sleep(self.delay)

    def hold(self) -> None:

        while self.paused:
            time.sleep(self.delay)

async def async_loop[T](
        controller: Controller,
        target: Callable[..., Awaitable[T]],
        args: Iterable = None,
        kwargs: dict[str, ...] = None,
        results: list[T] = None
) -> list[T]:

    if results is None:
        results = []

    while controller.running:
        await controller.async_hold()

        results.append(await target(*(args or ()), **(kwargs or {})))

    return results

def loop[T](
        controller: Controller,
        target: Callable[..., T],
        args: Iterable = None,
        kwargs: dict[str, ...] = None,
        results: list[T] = None
) -> list[T]:

    if results is None:
        results = []

    while controller.running:
        controller.hold()

        results.append(target(*(args or ()), **(kwargs or {})))

    return results
