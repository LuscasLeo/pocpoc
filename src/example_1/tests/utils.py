from typing import Callable, List

from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.handler import MessageHandler
from pocpoc.api.messages.message import Message, MessageMetadata


class FakeMessageDispatcher(MessageDispatcher):
    def __init__(self) -> None:
        self.dispatched_messages: List[Message] = []

    def dispatch(self, event: Message) -> None:
        self.dispatched_messages.append(event)


class FakeMessageHandler(MessageHandler):
    def __init__(self, handler: Callable[[MessageMetadata, Message], None]) -> None:
        self.handler = handler

    def handle_message(
        self, message_metadata: MessageMetadata, message: Message
    ) -> None:
        self.handler(message_metadata, message)
