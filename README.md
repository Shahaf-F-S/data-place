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

A definition of a data model. 
Can be either shared globally or reimplemented separately.
Also defines an async loop function that will be used to produce Data objects.
```python
from dataclasses import dataclass
import asyncio
import random
from uuid import uuid4
from dataplace import ModelIO, Controller

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
```

async socket based data sending server
```python
import asyncio
from dataplace import Sender, Controller, Callback, SpaceStore

store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

server = Sender.Socket.Server(host="127.0.0.1", port=5555)

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
```

async socket based data receiving client
```python
import asyncio
from dataplace import Receiver, Callback, SpaceStore

store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

client = Receiver.Socket.Client(
    host="127.0.0.1",
    port=5555,
    callbacks=[
        Callback(store.add, types={Data}),
        Callback(print, types={Data})
    ]
)

loop = asyncio.new_event_loop()
loop.create_task(client.start())
loop.run_forever()
```

async websocket based data sending server
```python
import asyncio
from dataplace import Sender, Controller, Callback, SpaceStore

store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

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
```

async websocket based data receiving client
```python
import asyncio
from dataplace import Receiver, Callback, SpaceStore

store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

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
```

async socket based data receiving server
```python
import asyncio
from dataplace import Receiver, Callback, SpaceStore

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
```

async socket based data sending client
```python
store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

client = Sender.Socket.Client(host="127.0.0.1", port=5555)

controller = Controller(
    callbacks=[
        Callback(store.add, types={Data}),
        Callback(client.call, types={Data}),
        Callback(print, types={Data})
    ]
)

loop = asyncio.new_event_loop()
loop.run_until_complete(client.start())
loop.create_task(produce(controller))
loop.run_forever()
```

async websocket based data receiving server
```python
import asyncio
from dataplace import Receiver, Callback, SpaceStore

store = SpaceStore[Data, int](Data, signature=lambda data: data.value)

server = Receiver.WebSocket.Server(
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
```

async websocket based data sending client
```python
import asyncio
from dataplace import Sender, Callback, SpaceStore

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
loop.run_until_complete(client.start())
loop.create_task(produce(controller))
loop.run_forever()
```