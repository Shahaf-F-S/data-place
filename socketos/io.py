# io.py

from typing import Self, overload, ClassVar
from abc import ABCMeta

__all__ = [
    "ModelIO",
    "getattrs"
]

def getattrs(obj: object, /) -> dict[str, ...]:

    if hasattr(obj, "__slots__"):
        return {
            attribute: getattr(obj, attribute)
            for attribute in obj.__slots__
        }

    elif hasattr(obj, "__dict__"):
        return obj.__dict__.copy()

    return {}

class ModelIO(metaclass=ABCMeta):

    TYPES: ClassVar[dict[str, [type["ModelIO"]]]] = {}
    TYPE: ClassVar[str] = "__type__"
    __model__: ClassVar[str | None] = None

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

        return getattrs(self)

    def labeled_dump(self) -> dict[str, ...]:

        data = self.dump()

        data[self.TYPE] = type(self).__name__

        return data

    @overload
    def copy(self) -> Self:

        pass

    @overload
    def copy(self, deep: bool = False) -> Self:

        pass
    
    def copy(self, **kwargs) -> Self:

        if kwargs.get("deep", False):
            return self.deepcopy()
        
        else:
            return self.shallowcopy()

    def shallowcopy(self) -> Self:

        data = self.__reduce__()

        return data[0](data[1][0], data[1][1], getattrs(self))

    def deepcopy(self) -> Self:

        data = self.__reduce__()

        state = getattrs(self)

        for key in state:
            for func in ("deepcopy", "deep_copy", "copy"):
                if hasattr(state[key], func):
                    try:
                        state[key] = getattr(state[key], func)()

                    except (TypeError, ValueError):
                        pass

        return data[0](data[1][0], data[1][1], state)
