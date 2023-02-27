from abc import ABC
from typing import Callable

from pocpoc.api.messages.message import Message, MessageMetadata


class MessageSubscriber(ABC):
    # @abstractmethod
    def listen(self, callback: Callable[[MessageMetadata, Message], None]) -> None:
        raise NotImplementedError()
