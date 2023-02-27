from abc import ABC

from pocpoc.api.messages.message import Message


class MessageDispatcher(ABC):
    # @abstractmethod
    def dispatch(self, message: Message) -> None:
        raise NotImplementedError()
