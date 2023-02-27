import logging
from abc import abstractmethod

from pocpoc.api.messages.handler import (
    MessageHandler,
    UnHandlableMessageException,
)
from pocpoc.api.messages.message import Message, MessageMetadata
from pocpoc.api.messages.rpc import RPC
from pocpoc.api.messages.rpc.errors import RPCServerErrorResponse
from pocpoc.api.di.class_initializer import ClassInitializer
from pocpoc.api.messages.rpc.map import RPCMap

logger = logging.getLogger(__name__)


@abstractmethod
class RPCMessageHandler(MessageHandler):
    def __init__(
        self,
        rpc_controller_map: RPCMap,
        class_initializer: ClassInitializer,
        # rpc_from_message_data: Callable[[MessageMetadata], Optional[RPC[Any, Any]]],
    ) -> None:
        self.rpc_controller_map = rpc_controller_map
        self.class_initializer = class_initializer

    def handle_message(self, event_data: MessageMetadata, message: Message) -> None:
        if not isinstance(message, RPC):
            raise UnHandlableMessageException(event_data, message, "Not an RPC")

        rpc_from_message = message

        if rpc_from_message is None:
            logger.warning("No rpc for message %s", event_data)
            return

        rpc_controller_class = self.rpc_controller_map.get_controller_by_name(
            rpc_from_message.message_type()
        )

        if rpc_controller_class is None:
            logger.warning("No rpc controller for rpc %s", event_data)
            return

        try:
            rpc_controller = self.class_initializer.get_instance(rpc_controller_class)
        except Exception as e:
            logger.error(
                "Error instantiating rpc controller %s for rpc %s",
                rpc_controller_class,
                event_data,
            )
            logger.exception(e)
            return

        try:
            result = rpc_controller.execute(rpc_from_message.get_input())

            self.reply(result)
        except Exception as e:
            logger.critical(
                "Error handling rpc %s with rpc controller %s",
                event_data,
                "{}.{}".format(
                    rpc_controller_class.__module__, rpc_controller_class.__name__
                ),
                exc_info=e,
            )

            self.reply(RPCServerErrorResponse(str(e)))

            logger.exception(e)

    @abstractmethod
    def reply(self, result: Message) -> None:
        raise NotImplementedError()
