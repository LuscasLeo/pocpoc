from datetime import datetime
from uuid import uuid4

from pocpoc.api.context_tracker.context_track_manager import (
    ContextTracker,
    get_current_context,
)
from pocpoc.api.messages.adapters.rmq import RMQConnectionFactory
from pocpoc.api.messages.codec import MessageKitEncoder
from pocpoc.api.messages.message import Message, MessageMetadata
from pocpoc.api.messages.dispatcher import MessageDispatcher


class RMQMessageDispatcher(MessageDispatcher):
    def __init__(
        self,
        connection_factory: RMQConnectionFactory,
        service_name: str,
        kit_encoder: MessageKitEncoder[bytes],
    ) -> None:
        self.connection_factory = connection_factory
        self._service_name = service_name
        self.kit_encoder = kit_encoder

    def dispatch(self, message: Message) -> None:
        rmq_connection = self.connection_factory.get_connection()

        channel = rmq_connection.channel()

        current_context = get_current_context()

        if current_context is None:
            current_context = ContextTracker(
                global_context_id=str(uuid4()),
                global_started=datetime.utcnow(),
                local_context_id=str(uuid4()),
                local_started=datetime.utcnow(),
                parent_context_id=None,
                service_name=self._service_name,
            )

        event_data = MessageMetadata(
            message_type=message.message_type(),
            tracked_context=current_context,
            sent_at=datetime.utcnow(),
        )

        body = self.kit_encoder.encode(event_data, message)

        channel.basic_publish(
            exchange=message.message_type(),
            routing_key="",
            body=body,
        )

        rmq_connection.close()
