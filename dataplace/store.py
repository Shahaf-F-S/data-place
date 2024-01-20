# store.py

from typing import (
    Iterable, Self, Generator, TypeVar, Hashable,
    Generic, Callable
)
import collections

__all__ = [
    "SpaceStore",
    "create_signatures"
]

_D = TypeVar("_D")
_S = TypeVar("_S", Hashable, Iterable[Hashable])

def create_signatures(
        key: _S, signature: list[_S] = None, signatures: list[_S] = None
) -> list[tuple[_S, ...]]:

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

class SpaceStore(Generic[_S, _D]):

    ITEM: type[_D] = None
    SIGNATURE: type[_S] = None

    def __init__(
            self,
            signature: Callable[[_D], _S],
            space: ... = None,
            item: type[_D] = None,
            records: Iterable[_D] = None
    ) -> None:

        self.space = space
        self.signature = signature
        self.item = item or self.ITEM

        self.store: dict[_S, list[_D]] = {}

        self.add_all(records or ())

    def __len__(self) -> int:

        return len(self.store)

    def __iter__(self) -> Generator[tuple[str, str], ..., ...]:

        yield from self.keys()

    def __contains__(self, item: tuple[str, str] | _D) -> bool:

        saved = None

        if isinstance(item, self.item):
            saved = item

            item = item.signature

        if not (
            isinstance(item, Hashable) and
            isinstance(item, collections.abc.Iterable)
        ):
            return False

        item = tuple(item)

        if len(item) != 2:
            return False

        return (
            (item in self.store) and
            (saved is None or saved in self.store[item])
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

    def keys(self) -> Generator[_S, ..., ...]:

        for keys in self.store.keys():
            if None in keys:
                continue

            yield keys

    def values(self) -> Generator[list[_D], ..., ...]:

        for keys, values in self.store.items():
            if None in keys:
                continue

            yield values

    def items(self) -> Generator[tuple[_S, list[_D]], ..., ...]:

        for keys, values in self.store.items():
            if None in keys:
                continue

            yield keys, values

    def signatures(self) -> set[_S]:

        return set(self.keys())

    def records(self) -> list[_D]:

        records = []

        for (exchange, symbol), values in self.store.items():
            if None in (exchange, symbol):
                continue

            records.extend(values)

        return records

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

    def containers(self, signature: _S, create: bool = True) -> list[list[_D]]:

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

    def add(self, record: _D) -> _D:

        for container in self.containers(self.signature(record)):
            container.append(record)

        return record

    def add_all(self, records: Iterable[_D]) -> Iterable[_D]:

        for record in records:
            self.add(record)

        return records

    def get(self, signature: _S, index: int = -1) -> _D:

        return self.store[signature][index]

    def get_all(self, signature: _S, copy: bool = True) -> list[_D]:

        data = self.store[signature]

        if copy:
            data = data.copy()

        return data

    def pop(self, signature: _S, index: int = -1) -> _D:

        record = self.get(signature, index=index)

        for container in self.containers(signature, create=False):
            i = index

            if i > 0:
                i = len(container) - i - 1

            container.pop(i)

        return record

    def pop_all(self, signature: _S) -> list[_D]:

        records = self.get_all(signature)

        for container in self.containers(signature, create=False):
            container.clear()

        return records

    def remove(self, record: _D) -> _D:

        for container in self.containers(record.signature, create=False):
            try:
                container.remove(record)

            except ValueError:
                pass

        return record

    def remove_all(self, records: Iterable[_D]) -> Iterable[_D]:

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
