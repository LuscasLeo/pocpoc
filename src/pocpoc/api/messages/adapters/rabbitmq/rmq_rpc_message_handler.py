import logging
from datetime import datetime

from pika import BasicProperties

from pocpoc.api.context_tracker.context_track_manager import (
    get_current_context,
)
from pocpoc.api.di.class_initializer import ClassInitializer
from pocpoc.api.messages.adapters.rabbitmq.rmq_message_subscriber import (
    get_current_message_data,
)
from pocpoc.api.messages.codec import MessageKitEncoder
from pocpoc.api.messages.message import Message, MessageMetadata
from pocpoc.api.messages.rpc.handler import RPCMessageHandler
from pocpoc.api.messages.rpc.map import RPCMap

logger = logging.getLogger(__name__)


class RabbitMQRPCMessageHandler(RPCMessageHandler):
    def __init__(
        self,
        rpc_map: RPCMap,
        class_initializer: ClassInitializer,
        kit_encoder: MessageKitEncoder[bytes],
    ) -> None:
        super().__init__(rpc_map, class_initializer)
        self.kit_encoder = kit_encoder

    def reply(self, result: Message) -> None:
        current_message = get_current_message_data()

        # TODO: Decouple context tracking from the message handler
        c = get_current_context()

        message_metadata = MessageMetadata(
            message_type=result.message_type(),
            tracked_context=c,
            sent_at=datetime.utcnow(),
        )

        body = self.kit_encoder.encode(message_metadata, result)

        current_message.channel.basic_publish(
            exchange="",
            routing_key=current_message.header_frame.reply_to,
            properties=BasicProperties(
                correlation_id=current_message.header_frame.correlation_id,
                timestamp=int(datetime.utcnow().timestamp()),
            ),
            body=body,
        )
