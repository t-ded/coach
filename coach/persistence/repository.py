from abc import ABC, abstractmethod
from typing import Iterable


class Repository[T](ABC):
    @abstractmethod
    def save(self, activity: T) -> None:
        ...

    @abstractmethod
    def save_many(self, activities: Iterable[T]) -> None:
        ...

    @abstractmethod
    def list_all(self) -> list[T]:
        ...
