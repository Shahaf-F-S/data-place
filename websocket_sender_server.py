# websocket_sender_server.py

import asyncio
import random
from uuid import uuid4
from dataclasses import dataclass

from dataplace import ModelIO, Sender, Controller, Callback, SpaceStore

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    id: str
    value: int

async def produce(controller: Controller) -> None:

    while controller.running:
        await controller.async_hold()
        await controller.async_callback(
            Data(id=str(uuid4()), value=random.randint(0, 9))
        )

        await asyncio.sleep(1)

def main() -> None:

    store = SpaceStore[int, Data](lambda data: data.value, Data)

    server = Sender.WebSocket.Server(host="127.0.0.1", port=5555)

    controller = Controller(
        callbacks=[
            Callback(store.add, types={Data}),
            Callback(server.call, types={Data}),
            Callback(print, types={Data})
        ]
    )

    loop = asyncio.new_event_loop()
    loop.create_task(produce(controller))
    loop.create_task(server.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
