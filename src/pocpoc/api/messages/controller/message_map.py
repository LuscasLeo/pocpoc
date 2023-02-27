import logging
from typing import Callable, Dict, Iterable, List, Optional, Type, TypeVar, cast

from pocpoc.api.messages.controller.message_controller import MessageController
from pocpoc.api.messages.map import MessageMap
from pocpoc.api.messages.message import Message

MESSAGE_TYPE = TypeVar("MESSAGE_TYPE", bound=Message)

logger = logging.getLogger(__name__)


class MessageControllerMap(MessageMap):
    def __init__(self) -> None:
        super().__init__()
        self.message_controller_map: Dict[
            Type[Message], List[Type[MessageController[Message]]]
        ] = {}
        self.message_type_by_name: Dict[str, Type[Message]] = {}
        self.message_controllers_by_type_name: Dict[
            str, List[Type[MessageController[Message]]]
        ] = {}
        self.hooks: Dict[Type[Message], List[Callable[[Message], None]]] = {}

    def register(
        self,
        message_type: Type[MESSAGE_TYPE],
        *handlers: Type[MessageController[MESSAGE_TYPE]],
    ) -> None:
        super().register_messages(message_type)
        self.message_controller_map.setdefault(message_type, []).extend(handlers)  # type: ignore

        logger.debug(
            f"Registered message type {message_type.message_type()} with handlers {[handler.__module__ + '.' + handler.__name__ for handler in handlers]}"
        )

        self.message_type_by_name[message_type.message_type()] = message_type
        self.message_controllers_by_type_name.setdefault(
            message_type.message_type(), []
        ).extend(cast(Iterable[Type[MessageController[Message]]], handlers))

    def get_controllers(
        self, message_type: str
    ) -> Optional[List[Type[MessageController[Message]]]]:
        return self.message_controllers_by_type_name.get(message_type)

    def get_message_type(self, message_type_name: str) -> Optional[Type[Message]]:
        return (
            self.message_type_by_name[message_type_name]
            if message_type_name in self.message_type_by_name
            else None
        )

    def register_hook(
        self, message_type: Type[MESSAGE_TYPE], hook: Callable[[MESSAGE_TYPE], None]
    ) -> None:
        super().register_messages(message_type)
        self.hooks.setdefault(message_type, []).append(
            cast(Callable[[Message], None], hook)
        )
