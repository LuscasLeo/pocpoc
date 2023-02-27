import logging
import signal
from contextlib import suppress
from typing import Any, Optional

from pocpoc.api.context_tracker.context_track_manager import (
    init_new_context,
)
from pocpoc.api.messages.adapters.json.json_kit_codec import (
    JsonMessageKitDecoder,
    JsonMessageKitEncoder,
)
from pocpoc.api.messages.adapters.json.json_message_codec import (
    JsonMessageDecoder,
    JsonMessageEncoder,
)
from pocpoc.api.messages.adapters.json.json_message_metadata_codec import (
    JsonMessageMetadataDecoder,
    JsonMessageMetadataEncoder,
)
from pocpoc.api.messages.adapters.rabbitmq.rmq_message_dispatcher import (
    RMQMessageDispatcher,
)
from pocpoc.api.messages.adapters.rabbitmq.rmq_message_subscriber import (
    RMQMessageSubscriber,
)
from pocpoc.api.messages.adapters.rabbitmq.rmq_rpc_client import (
    RMQRPCClient,
)
from pocpoc.api.messages.adapters.rabbitmq.rmq_rpc_message_handler import (
    RabbitMQRPCMessageHandler,
)
from pocpoc.api.messages.adapters.rabbitmq.rmq_utils import (
    register_messages_as_exchange_to_queue,
)
from pocpoc.api.messages.adapters.rmq import RMQConnectionFactory
from pocpoc.api.messages.codec import (
    MessageKitDecoder,
    MessageKitEncoder,
)
from pocpoc.api.messages.events.handler import EventMessageHandler
from pocpoc.api.messages.handler import UnHandlableMessageException
from pocpoc.api.messages.map import MessageMap
from pocpoc.api.messages.message import Message, MessageMetadata
from pocpoc.api.microservices import (
    Container,
    ContainerHandler,
    GracefulKiller,
)

logger = logging.getLogger(__name__)


class RabbitMQHandler(ContainerHandler):
    kit_encoder: Optional[MessageKitEncoder[bytes]] = None
    kit_decoder: Optional[MessageKitDecoder[bytes]] = None

    def __init__(self, service_queue: str, connection_factory: RMQConnectionFactory):
        super().__init__()
        self.connection_factory = connection_factory
        self.service_queue = service_queue

    def use_json_kit_codec(self, encoding: str) -> "RabbitMQHandler":
        def hook(container: Container) -> None:
            self.kit_encoder = JsonMessageKitEncoder(
                JsonMessageMetadataEncoder(encoding), JsonMessageEncoder(encoding)
            )
            self.kit_decoder = JsonMessageKitDecoder(
                JsonMessageMetadataDecoder(encoding),
                JsonMessageDecoder(container.get_message_map(), encoding),
            )

        self.before_start(hook)
        return self

    def _run(self, container: Container) -> Any:
        if self.kit_encoder is None or self.kit_decoder is None:
            raise RuntimeError(
                "kit_encoder is not set. Please use setup_kit_codec() first."
            )

        rpc_handler = RabbitMQRPCMessageHandler(
            container._rpc_map,
            container.get_class_initializer(),
            self.kit_encoder,
        )

        event_handler = EventMessageHandler(
            container._event_map,
            container._dependency_injection_manager,
        )

        with self.connection_factory.get_connection() as connection:
            with connection.channel() as channel:
                channel.basic_qos(prefetch_count=1)

                def on_exit() -> None:
                    channel.cancel()
                    connection.close()

                GracefulKiller.on_exit(on_exit)

                register_messages_as_exchange_to_queue(
                    container.get_message_map().get_messages().values(),
                    self.service_queue,
                    channel,
                )
                channel.queue_declare(queue=self.service_queue, durable=True)

                subscriber = RMQMessageSubscriber(
                    channel,
                    self.service_queue,
                    self.kit_decoder,
                )

                def on_alarm(signum: int, frame: Any) -> None:
                    raise TimeoutError("Timeout", signum, frame)

                signal.signal(signal.SIGALRM, on_alarm)

                def on_message(
                    message_metadata: MessageMetadata, message: Message
                ) -> None:
                    # signal.alarm(0)

                    try:
                        with init_new_context(
                            container._service_name,
                            message_metadata.tracked_context,
                        ):
                            with suppress(UnHandlableMessageException):
                                rpc_handler.handle_message(message_metadata, message)
                    except TimeoutError:
                        logger.error(
                            "Timeout while rpc handling message %s",
                            message_metadata,
                        )

                    # signal.alarm(0)

                    # signal.alarm(10)

                    try:
                        with init_new_context(
                            container._service_name,
                            message_metadata.tracked_context,
                        ):
                            with suppress(UnHandlableMessageException):
                                event_handler.handle_message(message_metadata, message)

                    except TimeoutError:
                        logger.error(
                            "Timeout while event handling message %s",
                            message_metadata,
                        )

                    # signal.alarm(0)

                subscriber.listen(on_message)


def create_rmq_json_rpc_client(
    service_name: str,
    connection_factory: RMQConnectionFactory,
    encoding: str,
    message_map: MessageMap,
) -> RMQRPCClient:
    return RMQRPCClient(
        service_name,
        connection_factory,
        JsonMessageKitEncoder(
            JsonMessageMetadataEncoder(encoding), JsonMessageEncoder(encoding)
        ),
        JsonMessageKitDecoder(
            JsonMessageMetadataDecoder(encoding),
            JsonMessageDecoder(message_map, encoding),
        ),
    )


def create_rmq_json_message_dispatcher(
    service_name: str,
    connection_factory: RMQConnectionFactory,
    encoding: str,
) -> RMQMessageDispatcher:
    return RMQMessageDispatcher(
        connection_factory,
        service_name,
        JsonMessageKitEncoder(
            JsonMessageMetadataEncoder(encoding), JsonMessageEncoder(encoding)
        ),
    )
