import logging
from typing import Callable, Dict, Iterable, List, Optional, Type, TypeVar, cast

from pocpoc.api.messages.events.event_controller import EventController
from pocpoc.api.messages.map import MessageMap
from pocpoc.api.messages.message import Message

MESSAGE_TYPE = TypeVar("MESSAGE_TYPE", bound=Message)

logger = logging.getLogger(__name__)


class EventMap(MessageMap):
    def __init__(self) -> None:
        super().__init__()
        self.event_controller_map: Dict[
            Type[Message], List[Type[EventController[Message]]]
        ] = {}
        self.event_type_by_name: Dict[str, Type[Message]] = {}
        self.event_controllers_by_type_name: Dict[
            str, List[Type[EventController[Message]]]
        ] = {}
        self.hooks: Dict[Type[Message], List[Callable[[Message], None]]] = {}

    def register(
        self,
        event_type: Type[MESSAGE_TYPE],
        *handlers: Type[EventController[MESSAGE_TYPE]],
    ) -> None:
        super().register_messages(event_type)
        self.event_controller_map.setdefault(event_type, []).extend(handlers)  # type: ignore

        logger.debug(
            f"Registered event type {event_type.message_type()} with handlers {[handler.__module__ + '.' + handler.__name__ for handler in handlers]}"
        )

        self.event_type_by_name[event_type.message_type()] = event_type
        self.event_controllers_by_type_name.setdefault(
            event_type.message_type(), []
        ).extend(cast(Iterable[Type[EventController[Message]]], handlers))

    def get_controllers(
        self, event_type: str
    ) -> Optional[List[Type[EventController[Message]]]]:
        return self.event_controllers_by_type_name.get(event_type)

    def get_event_type(self, event_type_name: str) -> Optional[Type[Message]]:
        return (
            self.event_type_by_name[event_type_name]
            if event_type_name in self.event_type_by_name
            else None
        )

    def register_hook(
        self, event_type: Type[MESSAGE_TYPE], hook: Callable[[MESSAGE_TYPE], None]
    ) -> None:
        super().register_messages(event_type)
        self.hooks.setdefault(event_type, []).append(
            cast(Callable[[Message], None], hook)
        )
