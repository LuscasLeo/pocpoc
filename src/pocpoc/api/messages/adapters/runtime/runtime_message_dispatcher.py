from typing import Callable

from pocpoc.api.messages.message import Message
from pocpoc.api.messages.dispatcher import MessageDispatcher


class RuntimeEventDispatcher(MessageDispatcher):
    def __init__(
        self,
        callback: Callable[[Message], None],
    ) -> None:
        self.callback = callback

    def dispatch(self, event: Message) -> None:
        self.callback(event)
