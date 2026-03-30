from abc import ABC
from abc import abstractmethod
from typing import Optional


class ContextSection(ABC):
    @property
    @abstractmethod
    def header(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def render(self) -> Optional[str]:
        raise NotImplementedError
