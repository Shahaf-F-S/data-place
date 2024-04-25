# store.py

from typing import Iterable, Self, Generator, Hashable, Callable
import collections

__all__ = [
    "SpaceStore",
    "create_signatures"
]

def create_signatures[S](
        key: S, signature: list[S] = None, signatures: list[S] = None
) -> list[tuple[S, ...]]:

    if signature is None:
        signature = []

    if signatures is None:
        signatures = []

    if (
        isinstance(key, (str, bytes)) or
        not isinstance(key, collections.abc.Iterable)
    ):
        return [key, None]

    if not isinstance(key, tuple):
        key = tuple(key)

    if not key:
        signatures.append(tuple(signature))

        return signatures

    for sub_signature in create_signatures(key[0]):
        create_signatures(
            key[1:],
            [*signature, sub_signature],
            signatures
        )

    return signatures

class SpaceStore[S: Hashable | Iterable[Hashable], D]:

    def __init__(self, signature: Callable[[D], S], item: type[D]) -> None:

        self.item = item
        self.signature = signature

        self.store: dict[tuple[S, ...], list[D]] = {}

    def __len__(self) -> int:

        return len(self.store)

    def __iter__(self) -> Generator[S, ..., ...]:

        yield from self.keys()

    def __contains__(self, item: S | D) -> bool:

        if (
            isinstance(item, Hashable) and
            not isinstance(item, collections.abc.Iterable)
        ):
            item = (item,)

        if (
            not isinstance(item, Hashable) and
            isinstance(item, collections.abc.Iterable)
        ):
            item = tuple(item)

        return (
            (item in self.store) and
            (item is None or item in self.store[item])
        )

    def __add__(self, other: ...) -> Self:

        if not isinstance(other, type(self)):
            raise TypeError(
                f"both objects must be {type(self)} "
                f"instances for addition, received: {type(other)}"
            )

        return self.union(other)

    def __sub__(self, other: ...) -> Self:

        if not isinstance(other, type(self)):
            raise TypeError(
                f"both objects must be {type(self)} "
                f"instances for subtraction, received: {type(other)}"
            )

        return self.difference(other)

    def keys(self) -> Generator[S, ..., ...]:

        for keys in self.store.keys():
            if None in keys:
                continue

            yield keys

    def values(self) -> Generator[list[D], ..., ...]:

        for keys, values in self.store.items():
            if None in keys:
                continue

            yield values

    def items(self) -> Generator[tuple[S, list[D]], ..., ...]:

        for keys, values in self.store.items():
            if None in keys:
                continue

            yield keys, values

    def signatures(self) -> set[S]:

        return set(self.keys())

    @staticmethod
    def validate_signature(signature: ...) -> tuple:

        if not isinstance(signature, collections.abc.Iterable):
            signature = (signature,)

        if not (
            isinstance(signature, collections.abc.Iterable) and
            all(isinstance(key, Hashable) for key in signature)
        ):
            raise TypeError("Signature must be en iterable of hashable values.")

        return tuple(signature)

    def containers(self, signature: S, create: bool = True) -> list[list[D]]:

        signature = self.validate_signature(signature)

        signatures = create_signatures(signature)

        if create:
            return [
                self.store.setdefault(sig, [])
                for sig in signatures
            ]

        else:
            return [
                self.store[sig]
                for sig in signatures
                if sig in self.store
            ]

    def add(self, record: D) -> D:

        for container in self.containers(self.signature(record)):
            container.append(record)

        return record

    def add_all(self, records: Iterable[D]) -> Iterable[D]:

        for record in records:
            self.add(record)

        return records

    def get(self, signature: S, index: int = -1) -> D:

        return self.store[signature][index]

    def get_all(self, signature: S, copy: bool = True) -> list[D]:

        data = self.store[signature]

        if copy:
            data = data.copy()

        return data

    def pop(self, signature: S, index: int = -1) -> D:

        record = self.get(signature, index=index)

        for container in self.containers(signature, create=False):
            i = index

            if i > 0:
                i = len(container) - i - 1

            container.pop(i)

        return record

    def pop_all(self, signature: S) -> list[D]:

        records = self.get_all(signature)

        for container in self.containers(signature, create=False):
            container.clear()

        return records

    def remove(self, record: D) -> D:

        for container in self.containers(record.signature, create=False):
            try:
                container.remove(record)

            except ValueError:
                pass

        return record

    def remove_all(self, records: Iterable[D]) -> Iterable[D]:

        for record in records:
            self.remove(record)

        return records

    def extend(self, store: Self) -> None:

        for signature in store.signatures():
            for c1, c2 in zip(
                self.containers(signature),
                store.containers(signature)
            ):
                c1.extend(c2)

    def reduce(self, store: Self) -> None:

        for signature in store.signatures():
            self.pop_all(signature)

    def difference(self, store: Self) -> Self:

        copy = self.copy()

        copy.reduce(store)

        return copy

    def symmetric_difference(self, store: Self) -> Self:

        copy = self.union(store)

        copy.reduce(self.intersection(store))

        return copy

    def empty(self) -> Self:

        builder = self.__reduce__()

        # noinspection PyTypeChecker
        data: dict[str, ...] = builder[1][2]

        data["store"] = {}

        return builder[0](*builder[1])

    def union(self, store: Self) -> Self:

        copy = self.empty()

        copy.extend(self)
        copy.extend(store)

        return copy

    def intersection(self, store: Self) -> Self:

        copy = self.empty()

        store_signatures = store.signatures()

        for signature in self.signatures():
            if signature in store_signatures:
                records1 = self.get_all(signature, copy=False)
                records2 = store.get_all(signature, copy=False)

                records = []

                for record in records1:
                    if record not in records2:
                        records.append(record)

                for container in copy.containers(*signature):
                    container.extend(records)

        return copy

    def clear(self) -> None:

        self.store.clear()

    def copy(self) -> Self:

        copy = self.empty()

        copy.extend(self)

        return copy
