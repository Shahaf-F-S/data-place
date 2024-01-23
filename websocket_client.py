# websocket_client.py

import asyncio
from dataclasses import dataclass

from dataplace import (
    ModelIO, ReceiverWebSocketClient, Callback, SpaceStore
)

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    value: int
    id: str

def main() -> None:
    """A function to run the main test."""

    store = SpaceStore[int, Data](signature=lambda data: data.value)

    client = ReceiverWebSocketClient(
        url="ws://127.0.0.1:5555",
        callbacks=[
            Callback(callback=lambda data: store.add(data), types={Data}),
            Callback(callback=lambda data: print(f"received: {data}"), types={Data})
        ]
    )

    loop = asyncio.new_event_loop()

    loop.create_task(client.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
