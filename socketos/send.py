# send.py

from abc import ABCMeta, abstractmethod
import asyncio
import json

# noinspection PyProtectedMember
from websockets.legacy.server import serve, WebSocketServerProtocol, Serve
# noinspection PyProtectedMember
from websockets.legacy.client import WebSocketClientProtocol
from websockets.sync.client import connect, ClientConnection

from socketos.io import ModelIO
from socketos.callback import Callback
from socketos.base import BaseCommunicator

__all__ = [
    "encode",
    "SenderWebSocket",
    "SenderServer",
    "SenderSocket",
    "SenderClient",
    "SenderSocketServer",
    "SenderSocketClient",
    "SenderWebSocketServer",
    "SenderWebSocketClient",
    "BaseSender"
]

def encode(data: ModelIO) -> bytes:

    return json.dumps(data.labeled_json()).encode()

class BaseSender(BaseCommunicator, metaclass=ABCMeta):

    @abstractmethod
    async def send(self, data: ModelIO, **kwargs) -> None:

        pass

    async def handle(self, data: ModelIO, **kwargs) -> None:

        await self.send(data, **kwargs)

class SenderServer(BaseSender, metaclass=ABCMeta):

    DELAY = 0.0001

    def __init__(
            self,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None
    ) -> None:

        self.queues: list[list[ModelIO]] = []

        self.delay = delay or self.DELAY

        BaseSender.__init__(
            self,
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled
        )

    async def call(self, data: ModelIO) -> None:

        for queue in self.queues:
            queue.append(data)

    async def _handling_loop(self, **kwargs) -> None:

        queue: list[ModelIO] = []

        self.queues.append(queue)

        while self.running:
            await asyncio.sleep(self.delay)

            if self.paused:
                continue

            if queue:
                data = queue.pop(0)

                await self.handle(**kwargs, data=data)

        self.queues.remove(queue)

class SenderClient(BaseSender, metaclass=ABCMeta):

    pass

class SenderSocket(BaseSender, metaclass=ABCMeta):

    def __init__(
            self,
            host: str,
            port: int,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True
    ) -> None:

        self.host = host
        self.port = port

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled
        )

    async def send(
            self,
            data: ModelIO,
            reader: asyncio.StreamReader = None,
            writer: asyncio.StreamWriter = None
    ) -> None:
        """
        Receives the data from the senders.

        :param data: The data to send.
        :param reader: The data reader.
        :param writer: The data writer.
        """

        packet = encode(data)

        message = str(len(packet)).encode().rjust(16, b'0') + packet

        writer.write(message)

        await writer.drain()

    async def receive(
            self,
            reader: asyncio.StreamReader = None,
            writer: asyncio.StreamWriter = None
    ) -> None:
        """
        Receives the data from the senders.

        :param reader: The data reader.
        :param writer: The data writer.
        """

    async def handle(
            self,
            data: ModelIO,
            reader: asyncio.StreamReader = None,
            writer: asyncio.StreamWriter = None
    ) -> None:
        """
        Receives the data from the senders.

        :param data: The data to send.
        :param reader: The data reader.
        :param writer: The data writer.
        """

        await self.send(data, reader=reader, writer=writer)

WebSocket = WebSocketServerProtocol | WebSocketClientProtocol | ClientConnection

class SenderWebSocket(BaseSender, metaclass=ABCMeta):

    async def send(self, data: ModelIO, websocket: WebSocket = None) -> None:

        packet = encode(data)

        if not isinstance(websocket, ClientConnection):
            await websocket.send(packet)

        else:
            websocket.send(packet)

    async def receive(self, websocket: WebSocket = None) -> None:

        pass

    async def handle(self, data: ModelIO, websocket: WebSocket = None) -> None:

        await self.send(data, websocket=websocket)

class SenderSocketClient(SenderSocket, SenderClient):

    reader: asyncio.StreamReader | None = None
    writer: asyncio.StreamWriter | None = None

    async def call(self, data: ModelIO) -> None:

        await self.handle(data, writer=self.writer, reader=self.reader)

    async def connect(self) -> None:

        self.reader, self.writer = await asyncio.open_connection(
            host=self.host, port=self.port
        )

class SenderSocketServer(SenderServer, SenderSocket):

    server: asyncio.Server | None = None

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

        SenderServer.__init__(
            self,
            callbacks=callbacks,
            paused=paused,
            running=running,
            delay=delay,
            enabled=enabled
        )

        SenderSocket.__init__(
            self,
            callbacks=callbacks,
            paused=paused,
            running=running,
            host=host,
            port=port,
            enabled=enabled
        )

    async def _handling_loop(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Receives the data from the senders.

        :param reader: The data reader.
        :param writer: The data writer.
        """

        await super()._handling_loop(reader=reader, writer=writer)

    async def connect(self) -> None:

        self.server = await asyncio.start_server(
            self._handling_loop, self.host, self.port
        )

    async def start(self) -> None:

        await super().start()

        async with self.server:
            await self.server.serve_forever()

class SenderWebSocketClient(SenderClient, SenderWebSocket):

    client: ClientConnection | None = None

    def __init__(
            self,
            url: str,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True
    ) -> None:

        self.url = url

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled
        )

    async def call(self, data: ModelIO) -> None:

        await self.handle(data, self.client)

    async def connect(self) -> None:

        self.client = connect(self.url)

class SenderWebSocketServer(SenderServer, SenderWebSocket):

    server: Serve | None = None

    def __init__(
            self,
            host: str,
            port: int,
            callbacks: list[Callback] = None,
            paused: bool = False,
            running: bool = True,
            delay: float = None
    ) -> None:

        self.host = host
        self.port = port

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            delay=delay
        )

    async def _handling_loop(self, websocket: WebSocketServerProtocol) -> None:

        await super()._handling_loop(websocket=websocket)

    async def connect(self) -> None:

        self.server = serve(self._handling_loop, self.host, self.port)

    async def start(self) -> None:

        await super().start()

        async with self.server:
            await asyncio.Future()
