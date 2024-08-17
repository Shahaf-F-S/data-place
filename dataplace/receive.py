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
from dataplace.control import Controller
from dataplace.handler import Handler

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
    "decode",
    "Receiver"
]

def decode(data: bytes) -> ModelIO:

    return ModelIO.labeled_load(json.loads(data.decode()))

class BaseReceiver(BaseCommunicator, metaclass=ABCMeta):

    DELAY = 0.0001

    def __init__(
            self,
            callbacks: list[Callback] = None,
            controllers: list[Controller] = None,
            handler: Handler = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None,
            data: ... = None
    ) -> None:

        self.delay = delay or self.DELAY

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            controllers=controllers,
            handler=handler,
            data=data
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
            controllers: list[Controller] = None,
            handler: Handler = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None,
            data: ... = None
    ) -> None:

        self.host = host
        self.port = port

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            delay=delay,
            controllers=controllers,
            handler=handler,
            data=data
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

        controller = Controller(
            data=dict(kwargs=dict(reader=reader, writer=writer)),
            handler=self.handler
        )

        self.controllers.append(controller)

        while controller.running:
            await asyncio.sleep(self.delay)

            while controller.paused:
                continue

            with controller.handler:
                await self.handle(reader=reader, writer=writer)

            if controller.handler.caught and controller.handler.exit:
                controller.running = False

                break

        if controller in self.controllers:
            self.controllers.remove(controller)

type WebSocket = WebSocketServerProtocol | WebSocketClientProtocol

class ReceiverWebSocket(BaseReceiver, metaclass=ABCMeta):

    def __init__(
            self,
            url: str,
            callbacks: list[Callback] = None,
            controllers: list[Controller] = None,
            handler: Handler = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None,
            data: ... = None
    ) -> None:

        self.url = url

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            delay=delay,
            controllers=controllers,
            handler=handler,
            data=data
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

    async def close(self) -> None:

        self.writer.close()

        await self.writer.wait_closed()

class ReceiverSocketServer(ReceiverSocket, ReceiverServer):

    server: asyncio.Server | None = None

    async def connect(self) -> None:

        self.server = await asyncio.start_server(
            self._handling_loop, self.host, self.port
        )

    async def close(self) -> None:

        self.server.close()

        await self.server.wait_closed()

    async def start(self) -> None:

        await super().start()

        async with self.server:
            await self.server.serve_forever()

class ReceiverWebSocketClient(ReceiverWebSocket, ReceiverClient):

    client: Connect | None = None

    async def connect(self) -> None:

        self.client = connect(self.url)

    async def close(self) -> None:

        await self.client.protocol.close()

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
            protocol: str = "ws",
            callbacks: list[Callback] = None,
            controllers: list[Controller] = None,
            handler: Handler = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            delay: float = None,
            data: ... = None
    ) -> None:

        self.host = host
        self.port = port
        self.protocol = protocol

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            url=f"{protocol}://{host}:{port}",
            delay=delay,
            controllers=controllers,
            handler=handler,
            data=data
        )

    async def connect(self) -> None:

        self.server = serve(self._handling_loop, self.host, self.port)

    async def close(self) -> None:

        self.server.ws_server.close()

        await self.server.ws_server.wait_closed()

    async def start(self) -> None:

        await super().start()

        async with self.server:
            await asyncio.Future()

class Receiver:

    class Socket:

        Server = ReceiverSocketServer
        Client = ReceiverSocketClient

    class WebSocket:

        Server = ReceiverWebSocketServer
        Client = ReceiverWebSocketClient
