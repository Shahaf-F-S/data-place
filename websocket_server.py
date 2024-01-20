# websocket_server.py

import asyncio
import random
from uuid import uuid4
from dataclasses import dataclass

from dataplace import (
    ModelIO, SenderWebSocketServer, Controller, Callback, SpaceStore
)

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    id: str
    value: int

async def produce(controller: Controller) -> None:

    while controller.running:
        while controller.paused:
            await asyncio.sleep(0.0001)

        data = Data(id=str(uuid4()), value=random.randint(0, 9))

        print(f"produced: {data}")

        await controller.callback(data)

        await asyncio.sleep(1)

def main() -> None:
    """A function to run the main test."""

    store = SpaceStore[int, Data](item=Data, signature=lambda data: data.value)

    server = SenderWebSocketServer(host="127.0.0.1", port=5555)

    controller = Controller(
        callbacks=[
            Callback(callback=lambda data: store.add),
            Callback(callback=server.call)
        ]
    )

    loop = asyncio.new_event_loop()

    loop.create_task(produce(controller))
    loop.create_task(server.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
