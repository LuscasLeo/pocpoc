from abc import ABC

from pocpoc.api.messages.message import Message


class MessageDispatcher(ABC):
    # @abstractmethod
    def dispatch(self, event: Message) -> None:
        raise NotImplementedError()
