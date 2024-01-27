# socket_receiver_server.py

import asyncio
from dataclasses import dataclass

from dataplace import ModelIO, Receiver, Callback, SpaceStore

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    id: str
    value: int

def main() -> None:

    store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

    server = Receiver.Socket.Server(
        host="127.0.0.1",
        port=5555,
        callbacks=[
            Callback(store.add, types={Data}),
            Callback(print, types={Data})
        ]
    )

    loop = asyncio.new_event_loop()
    loop.create_task(server.start())
    loop.run_forever()

if __name__ == "__main__":
    main()
