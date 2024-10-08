# send.py

from abc import ABCMeta, abstractmethod
import asyncio
import json

# noinspection PyProtectedMember
from websockets.legacy.server import serve, WebSocketServerProtocol, Serve
# noinspection PyProtectedMember
from websockets.legacy.client import WebSocketClientProtocol
from websockets.sync.client import connect, ClientConnection

from dataplace.io import ModelIO
from dataplace.callback import Callback
from dataplace.base import BaseCommunicator
from dataplace.control import Controller
from dataplace.handler import Handler

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
    "BaseSender",
    "Sender"
]

def encode(data: ModelIO) -> bytes:

    return json.dumps(data.labeled_dump()).encode()

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
            controllers: list[Controller] = None,
            handler: Handler = None,
            paused: bool = False,
            running: bool = True,
            enabled: bool = True,
            save: bool = False,
            delay: float = None,
            data: ... = None
    ) -> None:

        BaseSender.__init__(
            self,
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            data=data,
            controllers=controllers,
            handler=handler
        )

        self.queues: list[list[ModelIO]] = []
        self.queue: list[ModelIO] = []

        self.delay = delay or self.DELAY
        self.save = save

    async def call(self, data: ModelIO) -> None:

        if not self.queues and self.save:
            self.queue.append(data)

        else:
            for queue in self.queues:
                queue.extend(self.queue)
                queue.append(data)

            self.queue.clear()

        await self.async_callback(data)

    async def _handling_loop(self, **kwargs) -> None:

        queue: list[ModelIO] = []

        controller = Controller(
            data=dict(kwargs=kwargs, queue=queue),
            handler=self.handler
        )

        self.controllers.append(controller)

        self.queues.append(queue)

        while controller.running:
            await asyncio.sleep(self.delay)

            if controller.paused:
                continue

            if queue:
                data = queue.pop(0)

                with controller.handler:
                    await self.handle(**kwargs, data=data)

                if controller.handler.caught and controller.handler.exit:
                    controller.running = False

                    break

        if queue in self.queues:
            self.queues.remove(queue)

        if controller in self.controllers:
            self.controllers.remove(controller)

class SenderClient(BaseSender, metaclass=ABCMeta):

    pass

class SenderSocket(BaseSender, metaclass=ABCMeta):

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
            data: ... = None
    ) -> None:

        self.host = host
        self.port = port

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            enabled=enabled,
            controllers=controllers,
            handler=handler,
            data=data
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

type WebSocket = WebSocketServerProtocol | WebSocketClientProtocol | ClientConnection

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

    async def close(self) -> None:

        self.writer.close()

        await self.writer.wait_closed()

class SenderSocketServer(SenderServer, SenderSocket):

    server: asyncio.Server | None = None

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
            save: bool = False,
            delay: float = None,
            data: ... = None
    ) -> None:

        SenderServer.__init__(
            self,
            callbacks=callbacks,
            paused=paused,
            running=running,
            delay=delay,
            save=save,
            enabled=enabled,
            controllers=controllers,
            handler=handler,
            data=data
        )

        SenderSocket.__init__(
            self,
            callbacks=callbacks,
            paused=paused,
            running=running,
            host=host,
            port=port,
            enabled=enabled,
            controllers=controllers,
            handler=handler,
            data=data
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

    async def close(self) -> None:

        self.server.close()

        await self.server.wait_closed()

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

    async def close(self) -> None:

        self.client.close()

class SenderWebSocketServer(SenderServer, SenderWebSocket):

    server: Serve | None = None

    def __init__(
            self,
            host: str,
            port: int,
            callbacks: list[Callback] = None,
            controllers: list[Controller] = None,
            handler: Handler = None,
            paused: bool = False,
            running: bool = True,
            save: bool = False,
            delay: float = None,
            data: ... = None
    ) -> None:

        self.host = host
        self.port = port

        super().__init__(
            callbacks=callbacks,
            paused=paused,
            running=running,
            delay=delay,
            save=save,
            controllers=controllers,
            handler=handler,
            data=data
        )

    async def _handling_loop(self, websocket: WebSocketServerProtocol) -> None:

        await super()._handling_loop(websocket=websocket)

    async def connect(self) -> None:

        self.server = serve(self._handling_loop, self.host, self.port)

    async def close(self) -> None:

        self.server.ws_server.close()

        await self.server.ws_server.wait_closed()

    async def start(self) -> None:

        await super().start()

        async with self.server:
            await asyncio.Future()

class Sender:

    class Socket:

        Server = SenderSocketServer
        Client = SenderSocketClient

    class WebSocket:

        Server = SenderWebSocketServer
        Client = SenderWebSocketClient
