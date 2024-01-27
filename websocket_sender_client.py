# websocket_sender_client.py

import asyncio
from uuid import uuid4
import random
from dataclasses import dataclass

from dataplace import ModelIO, Sender, Callback, SpaceStore, Controller

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    id: str
    value: int

async def produce(controller: Controller) -> None:

    while controller.running:
        await controller.hold()
        await controller.async_callback(
            Data(id=str(uuid4()), value=random.randint(0, 9))
        )

        await asyncio.sleep(1)

def main() -> None:

    store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

    client = Sender.WebSocket.Client(url="ws://127.0.0.1:5555")

    controller = Controller(
        callbacks=[
            Callback(store.add, types={Data}),
            Callback(client.call, types={Data}),
            Callback(print, types={Data})
        ]
    )

    loop = asyncio.new_event_loop()
    loop.create_task(produce(controller))
    loop.create_task(client.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
