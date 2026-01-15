from abc import ABC, abstractmethod
from typing import Iterable

from coach.domain.models import Activity


class ActivityRepository(ABC):
    @abstractmethod
    def save(self, activity: Activity) -> None:
        ...

    @abstractmethod
    def save_many(self, activities: Iterable[Activity]) -> None:
        ...

    @abstractmethod
    def list_all(self) -> list[Activity]:
        ...
