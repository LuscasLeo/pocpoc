import logging

from pocpoc.api.di.class_initializer import ClassInitializer
from pocpoc.api.messages.events.event_map import EventMap
from pocpoc.api.messages.handler import (
    MessageHandler,
    UnHandlableMessageException,
)
from pocpoc.api.messages.message import Message, MessageMetadata

logger = logging.getLogger(__name__)


class EventMessageHandler(MessageHandler):
    def __init__(
        self,
        event_handler_map: EventMap,
        class_initializer: ClassInitializer,
    ) -> None:
        self.event_handler_map = event_handler_map
        self.class_initializer = class_initializer

    def handle_message(
        self, message_metadata: MessageMetadata, message: Message
    ) -> None:
        handlers_class = self.event_handler_map.get_controllers(message.message_type())

        if handlers_class is None:
            raise UnHandlableMessageException(message_metadata, message, "No handlers")

        for cls in handlers_class:
            try:
                handler = self.class_initializer.get_instance(cls)
            except Exception as e:
                logger.error(
                    "Error instantiating handler %s for message %s",
                    cls,
                    message_metadata,
                )
                logger.exception(e)
                continue

            try:
                handler.execute(message)
            except Exception as e:
                logger.critical(
                    "Error handling message %s with handler %s",
                    message_metadata,
                    "{}.{}".format(cls.__module__, cls.__name__),
                    exc_info=e,
                )
                logger.exception(e)
