# websocket_receiver_client.py

import asyncio
from dataclasses import dataclass

from dataplace import ModelIO, Receiver, Callback, SpaceStore

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    id: str
    value: int

def main() -> None:

    store = SpaceStore[int, Data](lambda data: data.value, Data)

    client = Receiver.WebSocket.Client(
        url="ws://127.0.0.1:5555",
        callbacks=[
            Callback(store.add, types={Data}),
            Callback(print, types={Data})
        ]
    )

    loop = asyncio.new_event_loop()
    loop.create_task(client.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
