# socket_sender_client.py

import asyncio
from uuid import uuid4
import random
from dataclasses import dataclass

from dataplace import (
    ModelIO, Sender, Callback, SpaceStore, Controller
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

    store = SpaceStore(signature=lambda data: data.value)

    client = Sender.Socket.Client(host="127.0.0.1", port=5555)

    controller = Controller(
        callbacks=[
            Callback(callback=store.add, types={Data}),
            Callback(callback=client.call, types={Data})
        ]
    )

    loop = asyncio.new_event_loop()
    loop.run_until_complete(client.start())
    loop.create_task(produce(controller))
    loop.run_forever()

if __name__ == "__main__":
    main()
