import logging
from datetime import datetime
from typing import Any, Optional, cast
from uuid import uuid4

import pika

from pocpoc.api.context_tracker.context_track_manager import (
    ContextTracker,
    get_current_context,
)
from pocpoc.api.messages.adapters.rmq import RMQConnectionFactory
from pocpoc.api.messages.codec import (
    MessageKitDecoder,
    MessageKitEncoder,
)
from pocpoc.api.messages.message import MessageMetadata
from pocpoc.api.messages.rpc import RPC, RPCClient, RPCInput, RPCOutput
from pocpoc.api.messages.rpc.errors import (
    RPCServerError,
    RPCServerErrorResponse,
)

logger = logging.getLogger(__name__)


class RMQRCPClientCaller:
    def __init__(
        self, connection: pika.BlockingConnection, exchange: str, input: bytes
    ) -> None:
        self.connection = connection
        self.exchange = exchange
        self.input = input
        self.response: Optional[bytes] = None
        self.correlation_id: Optional[str] = None

    def on_response(self, ch: Any, method: Any, props: Any, body: bytes) -> None:
        if self.correlation_id == props.correlation_id:
            self.response = body

    def call(self) -> bytes:
        channel = self.connection.channel()
        self.correlation_id = str(uuid4())

        result = channel.queue_declare(queue="", exclusive=True, durable=False)
        callback_queue = result.method.queue

        logger.debug(
            "Sending RPC request to exchange %s with correlation_id %s. Awaiting response on queue %s",
            self.exchange,
            self.correlation_id,
            callback_queue,
        )

        channel.basic_consume(
            queue=callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

        channel.basic_publish(
            exchange=self.exchange,
            routing_key="",
            properties=pika.BasicProperties(
                reply_to=callback_queue,
                correlation_id=self.correlation_id,
            ),
            body=self.input,
        )

        while self.response is None:
            logger.debug(
                "Waiting for RPC response for correlation_id %s", self.correlation_id
            )
            self.connection.process_data_events(time_limit=None)  # type: ignore

        logger.debug("RPC response received for correlation_id %s", self.correlation_id)

        return self.response


class RMQRPCClient(RPCClient):
    def __init__(
        self,
        service_name: str,
        rmq_connection_factory: RMQConnectionFactory,
        kit_encoder: MessageKitEncoder[bytes],
        kit_decoder: MessageKitDecoder[bytes],
    ) -> None:
        self.service_name = service_name
        self.rmq_connection_factory = rmq_connection_factory
        self.kit_encoder = kit_encoder
        self.kit_decoder = kit_decoder

    def submit(self, rpc: RPC[RPCInput, RPCOutput]) -> RPCOutput:
        with self.rmq_connection_factory.get_connection() as conn:
            current_context = get_current_context() or ContextTracker(
                global_context_id=str(uuid4()),
                parent_context_id=None,
                global_started=datetime.utcnow(),
                local_context_id=str(uuid4()),
                local_started=datetime.utcnow(),
                service_name=self.service_name,
            )

            message_metadata = MessageMetadata(
                message_type=rpc.message_type(),
                sent_at=datetime.utcnow(),
                tracked_context=current_context,
            )

            body = self.kit_encoder.encode(message_metadata, rpc)

            result = RMQRCPClientCaller(conn, rpc.message_type(), body).call()

            (
                __response_message_metadata,
                message,
            ) = self.kit_decoder.decode(result)

            if isinstance(message, RPCServerErrorResponse):
                raise RPCServerError(message)

            return cast(RPCOutput, message)
