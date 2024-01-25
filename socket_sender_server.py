# socket_sender_server.py

import asyncio
import random
from uuid import uuid4
from dataclasses import dataclass

from dataplace import (
    ModelIO, SenderSocketServer, Controller, Callback, SpaceStore
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

        await controller.async_callback(data)

        await asyncio.sleep(1)

def main() -> None:
    """A function to run the main test."""

    store = SpaceStore(item=Data, signature=lambda data: data.value)

    server = SenderSocketServer(host="127.0.0.1", port=5555)

    controller = Controller(
        callbacks=[
            Callback(callback=store.add, types={Data}),
            Callback(callback=server.call, types={Data})
        ]
    )

    loop = asyncio.new_event_loop()

    loop.create_task(produce(controller))
    loop.create_task(server.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
