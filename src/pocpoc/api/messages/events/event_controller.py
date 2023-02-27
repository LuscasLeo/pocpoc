from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pocpoc.api.messages.message import Message

MessageT = TypeVar("MessageT", bound=Message)


class EventController(ABC, Generic[MessageT]):
    @abstractmethod
    def execute(self, event: MessageT) -> None:
        raise NotImplementedError()
