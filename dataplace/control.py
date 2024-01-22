# control.py

from dataclasses import dataclass, field
import asyncio

from dataplace.io import ModelIO
from dataplace.callback import Callback
from dataplace.handler import Handler

__all__ = [
    "Controller"
]

Data = ModelIO | object

@dataclass
class Controller:

    callbacks: list[Callback] = field(default_factory=list)
    handler: Handler = None
    paused: bool = False
    running: bool = True
    enabled: bool = True

    def pause(self) -> None:

        self.paused = True

    def unpause(self) -> None:

        self.paused = False

    def stop(self) -> None:

        self.paused = False
        self.running = False

    def run(self) -> None:

        self.running = True

    def enable(self) -> None:

        self.enabled = True

    def disable(self) -> None:

        self.enabled = False

    async def async_callback(self, data: Data) -> None:

        if self.callbacks:
            await asyncio.gather(
                *(
                    callback.async_execute(data)
                    for callback in self.callbacks
                )
            )

    def callback(self, data: Data) -> None:

        if self.callbacks:
            all(callback.execute(data) for callback in self.callbacks)
