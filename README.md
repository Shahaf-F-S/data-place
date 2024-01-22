# data-place

> A powerful and flexible framework for designing async socket based data streaming and distribution systems, with automated parsing, dynamic data store and high-level control hooks.

Installation
-----------
````
pip install data-place
````

example
-----------
* integrates with dataclasses and pydantic as a side effect

websocket publisher server

```python
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

        await controller.async_callback(data)

        await asyncio.sleep(1)


store = SpaceStore[int, Data](item=Data, signature=lambda data: data.value)

server = SenderWebSocketServer(host="127.0.0.1", port=5555)

controller = Controller(
    callbacks=[
        Callback(async_callback=lambda data: store.add),
        Callback(async_callback=server.call)
    ]
)

loop = asyncio.new_event_loop()

loop.create_task(produce(controller))
loop.create_task(server.start())
loop.run_forever()
```

websocket subscriber client
```python
import asyncio
from dataclasses import dataclass

from dataplace import (
    ModelIO, ReceiverWebSocketClient, Callback, SpaceStore
)

@dataclass(slots=True, frozen=True)
class Data(ModelIO):

    value: int
    id: str

store = SpaceStore[int, Data](signature=lambda data: data.value)

client = ReceiverWebSocketClient(
    url="ws://127.0.0.1:5555",
    callbacks=[
        Callback(async_callback=lambda data: store.add(data)),
        Callback(async_callback=lambda data: print(f"received: {data}"))
    ]
)

loop = asyncio.new_event_loop()

loop.create_task(client.start())
loop.run_forever()
```