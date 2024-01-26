# socket_receiver_client.py

import asyncio
from dataclasses import dataclass

from dataplace import (
    ModelIO, Receiver, Callback, SpaceStore
)

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    id: str
    value: int

def main() -> None:
    """A function to run the main test."""

    store = SpaceStore(signature=lambda data: data.value)

    client = Receiver.Socket.Client(
        host="127.0.0.1",
        port=5555,
        callbacks=[
            Callback(callback=store.add, types={Data}),
            Callback(callback=lambda data: print(f"received: {data}"), types={Data})
        ]
    )

    loop = asyncio.new_event_loop()
    loop.create_task(client.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
