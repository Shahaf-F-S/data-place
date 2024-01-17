# handler.py

import warnings
from typing import Any, Callable, Iterable, Self
from dataclasses import dataclass

__all__ = [
    "Handler"
]

@dataclass
class Handler:
    """A class to handle operations."""

    success_callback: Callable[["Handler"], Any] = None
    exception_callback: Callable[["Handler"], Any] = None
    cleanup_callback: Callable[["Handler"], Any] = None
    exception_handler: Callable[["Handler", Exception], Any] = None
    exceptions: Iterable[type[Exception]] = None
    warn: bool = True
    catch: bool = True
    silence: bool = False
    proceed: bool = False
    exit: bool = False
    data: ... = None

    def __enter__(self) -> Self:
        """
        Enters the generator.

        :return: The generator object.
        """

        if self.success_callback is not None:
            self.success_callback(self)

        return self

    def __exit__(self, base: type[Exception], exception: Exception, traceback) -> bool:
        """
        Exits the generator with exception.

        :param base: The base type of the exception.
        :param exception: The exception object.
        :param traceback: The traceback object.
        """

        caught = False

        if None not in (base, exception, traceback):
            self.exit = True
            self.proceed = False

            if isinstance(exception, tuple(self.exceptions or ()) or Exception):
                caught = self.catch and True

                if self.exception_callback is not None:
                    self.exception_callback(self)

                if self.exception_handler is None:
                    if not self.silence:
                        message = f"{base.__name__}: {str(exception)}"

                        if self.warn:
                            warnings.warn(message)

                        else:
                            print(message)

                else:
                    self.exception_handler(self, exception)

            if self.cleanup_callback is not None:
                self.cleanup_callback(self)

        return caught

    def __call__(self, data: ... = None) -> Self:

        if data is None:
            data = self.data

        return Handler(
            success_callback=self.success_callback,
            exception_callback=self.exception_callback,
            cleanup_callback=self.cleanup_callback,
            exception_handler=self.exception_handler,
            exceptions=self.exceptions,
            warn=self.warn,
            catch=self.catch,
            silence=self.silence,
            data=data
        )
