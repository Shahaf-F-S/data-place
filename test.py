# test.py

from dataclasses import dataclass

from socketos.io import ModelIO

@dataclass(slots=True, frozen=True)
class A(ModelIO):

    a: int

def main() -> None:
    """A function to run the main test."""

    print(A(0))


if __name__ == "__main__":
    main()
