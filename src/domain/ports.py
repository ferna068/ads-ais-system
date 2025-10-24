from abc import ABC, abstractmethod
from typing import Callable, Awaitable
from src.domain.models import Aircraft, AISTrame

class IReceiver(ABC):
    @abstractmethod
    def register_callback(self, callback: Callable[[Aircraft], Awaitable[None]]) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

class ISender(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def send(self, message: str) -> None:
        pass

class IAISMessageBuilder(ABC):
    @abstractmethod
    def build_ais_type9_trame(self, aircraft: Aircraft) -> AISTrame:
        pass