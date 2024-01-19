# io.py

from typing import Self
from abc import ABCMeta

__all__ = [
    "ModelIO",
    "attributes"
]

def attributes(obj, /) -> dict[str, ...]:

    if hasattr(obj, "__slots__"):
        return {
            attribute: getattr(obj, attribute)
            for attribute in obj.__slots__
        }

    elif hasattr(obj, "__dict__"):
        return obj.__dict__.copy()

    return {}

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
                if base.load != ModelIO.load:
                    return base.load(data)

                else:
                    return base(**data)

            except (ValueError, TypeError, KeyError) as e:
                pass

        raise e

    def dump(self) -> dict[str, ...]:

        return attributes(self)

    def labeled_dump(self) -> dict[str, ...]:

        data = self.dump()

        data[self.TYPE] = type(self).__name__

        return data