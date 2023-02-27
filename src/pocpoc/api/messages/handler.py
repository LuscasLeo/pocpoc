import logging
from abc import ABC, abstractmethod

from pocpoc.api.messages.message import Message, MessageMetadata

logger = logging.getLogger(__name__)


class UnHandlableMessageException(Exception):
    def __init__(
        self, message_metadata: MessageMetadata, message: Message, reason: str
    ) -> None:
        self.message_metadata = message_metadata
        self.message = message
        self.reason = reason


class MessageHandler(ABC):
    @abstractmethod
    def handle_message(self, event_data: MessageMetadata, message: Message) -> None:
        raise NotImplementedError()
