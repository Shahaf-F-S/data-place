# base.py

from abc import ABCMeta, abstractmethod

from dataplace.callback import Callback
from dataplace.control import Controller
from dataplace.handler import Handler

__all__ = [
    "BaseCommunicator"
]

class BaseCommunicator(Controller, metaclass=ABCMeta):

    def __init__(
            self,
            callbacks: list[Callback] = None,
            controllers: list[Controller] = None,
            handler: Handler = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            data: ... = None
    ) -> None:

        if callbacks is None:
            callbacks = []

        if controllers is None:
            controllers = []

        self._connected = False
        self._closed = False

        super().__init__(
            callbacks=callbacks,
            controllers=controllers,
            paused=paused,
            running=running,
            enabled=enabled,
            handler=handler or Handler(exit=True),
            data=data
        )

    @property
    def connected(self) -> bool:

        return self._connected

    @property
    def closed(self) -> bool:

        return self._closed

    async def send(self, **kwargs) -> None:

        pass

    async def handle(self, **kwargs) -> None:

        pass

    async def receive(self, **kwargs) -> None:

        pass

    @abstractmethod
    async def connect(self) -> None:

        pass

    @abstractmethod
    async def close(self) -> None:

        pass

    async def _close(self) -> None:

        await self.close()

        self._closed = True
        self._connected = False

    async def _connect(self) -> None:

        await self.connect()

        self._connected = True

    async def stop(self) -> None:

        if self.connected and not self.closed:
            await self._close()

    async def start(self) -> None:

        if not self.connected:
            await self._connect()
