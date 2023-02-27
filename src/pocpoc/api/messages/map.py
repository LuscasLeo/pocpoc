import logging
from typing import Dict, Optional, Type

from pocpoc.api.messages.message import Message

logger = logging.getLogger(__name__)


class MessageMap:
    def __init__(self) -> None:
        self.__messages_by_type: Dict[str, Type[Message]] = {}

    def register_messages(self, *messages: Type[Message]) -> None:
        for message in messages:
            if message.message_type() in self.__messages_by_type:
                logger.warning(
                    f"Message {message.message_type()} from {message.__module__}.{message.__name__} "
                    f"overrides {self.__messages_by_type[message.message_type()].__module__}."
                    f"{self.__messages_by_type[message.message_type()].__name__}"
                )
            self.__messages_by_type[message.message_type()] = message
            logger.debug(
                f"Registered message {message.message_type()} from {message.__module__}.{message.__name__}"
            )

    def get_message_type(self, message_type_name: str) -> Optional[Type[Message]]:
        return (
            self.__messages_by_type[message_type_name]
            if message_type_name in self.__messages_by_type
            else None
        )

    @staticmethod
    def join_maps(*maps: "MessageMap") -> "MessageMap":
        joined_map = MessageMap()
        for map in maps:
            joined_map.register_messages(*map.__messages_by_type.values())
        return joined_map

    def get_messages(self) -> Dict[str, Type[Message]]:
        return self.__messages_by_type

    def fill_from_message_map(self, message_map: "MessageMap") -> None:
        self.__messages_by_type.update(message_map.__messages_by_type)
