# receive.py

from abc import ABCMeta, abstractmethod
import asyncio
import json

# noinspection PyProtectedMember
from websockets.legacy.server import serve, WebSocketServerProtocol, Serve
# noinspection PyProtectedMember
from websockets.legacy.client import connect, Connect, WebSocketClientProtocol

from dataplace.io import ModelIO
from dataplace.callback import Callback
from dataplace.base import BaseCommunicator

__all__ = [
    "ReceiverSocket",
    "ReceiverSocketServer",
    "ReceiverSocketClient",
    "ReceiverWebSocketServer",
    "ReceiverWebSocketClient",
    "ReceiverClient",
    "ReceiverServer",
    "ReceiverWebSocket",
    "BaseReceiver",
    "decode"
]

def decode(data: bytes) -> ModelIO:

    return ModelIO.labeled_load(json.loads(data.decode()))

class BaseReceiver(BaseCommunicator, metaclass=ABCMeta):

    DELAY = 0.0001

    def __init__(
            self,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None
    ) -> None:

        self.delay = delay or self.DELAY

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled
        )

    @abstractmethod
    async def receive(self, **kwargs) -> None:

        pass

    async def handle(self, **kwargs) -> None:

        await self.receive(**kwargs)

class ReceiverServer(BaseReceiver, metaclass=ABCMeta):

    pass

class ReceiverClient(BaseReceiver, metaclass=ABCMeta):

    pass

class ReceiverSocket(BaseReceiver, metaclass=ABCMeta):

    def __init__(
            self,
            host: str,
            port: int,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None
    ) -> None:

        self.host = host
        self.port = port

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            delay=delay
        )

    async def send(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:

        pass

    async def receive(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:

        buffer_message = await reader.read(16)

        if not buffer_message:
            return

        buffer = int(buffer_message)

        if not buffer:
            return

        data = await reader.read(buffer)

        record = decode(data)

        await self.async_callback(data=record)

    async def _handling_loop(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:

        while self.running:
            await asyncio.sleep(self.delay)

            while self.paused:
                continue

            await self.handle(reader=reader, writer=writer)

WebSocket = WebSocketServerProtocol | WebSocketClientProtocol

class ReceiverWebSocket(BaseReceiver, metaclass=ABCMeta):

    def __init__(
            self,
            url: str,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None
    ) -> None:

        self.url = url

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            delay=delay
        )

    async def receive(self, websocket: WebSocket = None) -> None:

        data = await websocket.recv()

        record = decode(data)

        await self.async_callback(data=record)

    async def send(self, websocket: WebSocket = None) -> None:

        pass

    async def handle(self, websocket: WebSocket = None) -> None:

        await self.receive(websocket=websocket)

    async def _handling_loop(self, websocket: WebSocket = None) -> None:

        while self.running:
            await asyncio.sleep(self.delay)

            while self.paused:
                continue

            await self.handle(websocket=websocket)

class ReceiverSocketClient(ReceiverSocket, ReceiverClient):

    reader: asyncio.StreamReader | None = None
    writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:

        self.reader, self.writer = await asyncio.open_connection(
            host=self.host, port=self.port
        )

    async def start(self) -> None:

        await self.connect()

        self.running = True

        await self._handling_loop(
            reader=self.reader, writer=self.writer
        )

class ReceiverSocketServer(ReceiverSocket, ReceiverServer):

    server: asyncio.Server | None = None

    async def connect(self) -> None:

        self.server = await asyncio.start_server(
            self._handling_loop, self.host, self.port
        )

    async def start(self) -> None:

        await super().start()

        async with self.server:
            await self.server.serve_forever()

class ReceiverWebSocketClient(ReceiverWebSocket, ReceiverClient):

    client: Connect | None = None

    async def connect(self) -> None:

        self.client = connect(self.url)

    async def start(self) -> None:

        await super().start()

        async with self.client as websocket:
            await self._handling_loop(websocket=websocket)

class ReceiverWebSocketServer(ReceiverWebSocket, ReceiverServer):

    server: Serve | None = None

    def __init__(
            self,
            host: str,
            port: int,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None
    ) -> None:

        self.host = host
        self.port = port

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            url=f"ws://{host}:{port}",
            delay=delay
        )

    async def connect(self) -> None:

        self.server = serve(self._handling_loop, self.host, self.port)

    async def start(self) -> None:

        await super().start()

        async with self.server:
            await asyncio.Future()
