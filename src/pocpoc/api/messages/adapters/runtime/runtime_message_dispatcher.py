from typing import Callable

from pocpoc.api.messages.message import Message
from pocpoc.api.messages.dispatcher import MessageDispatcher


class RuntimeMessageDispatcher(MessageDispatcher):
    def __init__(
        self,
        callback: Callable[[Message], None],
    ) -> None:
        self.callback = callback

    def dispatch(self, message: Message) -> None:
        self.callback(message)
