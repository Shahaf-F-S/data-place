# io.py

from typing import Self
from abc import ABCMeta, abstractmethod

__all__ = [
    "ModelIO"
]

class ModelIO(metaclass=ABCMeta):

    TYPES: dict[str, [type["ModelIO"]]] = {}

    TYPE = "__type__"

    __model__: str = None

    def __init_subclass__(cls, **kwargs) -> object:

        cls.TYPES.setdefault(
            cls.__model__ or cls.__name__, []
        ).insert(0, cls)

        return super().__init_subclass__(**kwargs)

    @classmethod
    @abstractmethod
    def load(cls, data: dict[str, ...]) -> Self:

        return cls.labeled_load(data)

    @classmethod
    def labeled_load(cls, data: dict[str, ...]) -> Self:

        if cls.TYPE not in data:
            raise KeyError(
                f"{cls.TYPE} must be present in a labeled "
                f"JSON data of a {ModelIO} subclass."
            )

        e = None

        for base in cls.TYPES[data[cls.TYPE]]:
            try:
                return base.load(data)

            except (ValueError, TypeError, KeyError) as e:
                pass

        raise e

    @abstractmethod
    def json(self) -> dict[str, ...]:

        pass

    def labeled_json(self) -> dict[str, ...]:

        data = self.json()

        data[self.TYPE] = type(self).__name__

        return data