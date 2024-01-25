# io.py

from typing import Self, overload, ClassVar
from abc import ABCMeta

__all__ = [
    "ModelIO",
    "getattrs"
]

def getattrs(obj: object, /) -> dict[str, ...]:

    data = {}

    if hasattr(obj, "__slots__"):
        data.update(
            {
                attribute: getattr(obj, attribute)
                for attribute in obj.__slots__
            }
        )

    if hasattr(obj, "__dict__"):
        data.update(obj.__dict__)

    return data

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
    def labeled_load(cls, data: dict[str, ...]) -> Self:

        if cls.TYPE not in data:
            raise KeyError(
                f"{cls.TYPE} must be present in a labeled "
                f"JSON data of a {ModelIO} subclass."
            )

        model_type = data.pop(cls.TYPE)

        if model_type not in cls.TYPES:
            raise KeyError(
                f"{model_type} is not recognized as a model type."
            )

        e = None

        for base in cls.TYPES[model_type]:
            return base.load(data)

        raise e

    @classmethod
    def load(cls, data: dict[str, ...]) -> Self:

        # noinspection PyArgumentList
        return cls(**data)

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
