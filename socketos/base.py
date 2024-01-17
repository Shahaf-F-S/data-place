# base.py

from abc import ABCMeta, abstractmethod

from socketos.callback import Callback
from socketos.control import Controller

__all__ = [
    "BaseCommunicator"
]

class BaseCommunicator(Controller, metaclass=ABCMeta):

    def __init__(
            self,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True
    ) -> None:

        if callbacks is None:
            callbacks = []

        self._connected = False

        super().__init__(
            callbacks=callbacks, paused=paused,
            running=running, enabled=enabled
        )

    @property
    def connected(self) -> bool:

        return self._connected

    async def send(self, **kwargs) -> None:

        pass

    async def handle(self, **kwargs) -> None:

        pass

    async def receive(self, **kwargs) -> None:

        pass

    @abstractmethod
    async def connect(self) -> None:

        pass

    async def _connect(self) -> None:

        await self.connect()

        self._connected = True

    async def start(self) -> None:

        if not self.connected:
            await self._connect()
