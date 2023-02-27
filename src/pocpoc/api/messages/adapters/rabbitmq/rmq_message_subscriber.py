import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Generator, Optional

from pika.adapters.blocking_connection import BlockingChannel

from pocpoc.api.messages.codec import MessageKitDecoder
from pocpoc.api.messages.message import Message, MessageMetadata
from pocpoc.api.messages.subscriber import MessageSubscriber
from pocpoc.api.microservices import GracefulKiller

logger = logging.getLogger(__name__)


@dataclass
class RMQCurrentMessageData:
    channel: BlockingChannel
    method_frame: Any
    header_frame: Any
    body: bytes


current_message_ctx = ContextVar[Optional[RMQCurrentMessageData]](
    "current_message_ctx", default=None
)


@contextmanager
def init_current_message_ctx(
    channel: BlockingChannel,
    method_frame: Any,
    header_frame: Any,
    body: bytes,
) -> Generator[None, None, None]:
    token = current_message_ctx.set(
        RMQCurrentMessageData(channel, method_frame, header_frame, body)
    )
    try:
        yield
    finally:
        current_message_ctx.reset(token)


def get_current_message_data() -> RMQCurrentMessageData:
    value = current_message_ctx.get()
    if value is None:
        raise RuntimeError("No current message data")

    return value


class RMQMessageSubscriber(MessageSubscriber):
    def __init__(
        self,
        channel: BlockingChannel,
        queue: str,
        kit_decoder: MessageKitDecoder[bytes],
    ):
        self.channel = channel
        self.queue = queue
        self.kit_decoder = kit_decoder

    def listen(self, callback: Callable[[MessageMetadata, Message], None]) -> None:
        def on_message(
            channel: BlockingChannel,
            method_frame: Any,
            props: Any,
            body: bytes,
        ) -> None:
            with GracefulKiller.wait_for_kill():
                if not GracefulKiller.should_continue():
                    logger.info("Gracefully stopping subscriber")
                    return

                try:
                    message_metadata, message = self.kit_decoder.decode(body)

                except Exception:
                    logger.exception(
                        "Error deserializing Message from rabbitmq message with delivery tag %s",
                        method_frame.delivery_tag or "unknown",
                    )
                    self.channel.basic_reject(method_frame.delivery_tag, requeue=False)
                    return

                try:
                    with init_current_message_ctx(channel, method_frame, props, body):
                        callback(message_metadata, message)

                    if method_frame.delivery_tag:
                        self.channel.basic_ack(method_frame.delivery_tag)
                except Exception:
                    if method_frame.delivery_tag is not None:
                        self.channel.basic_reject(
                            method_frame.delivery_tag, requeue=False
                        )

                    logger.exception(
                        "Error deserializing message from rabbitmq message with delivery tag %s",
                        method_frame.delivery_tag or "unknown",
                    )

        self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=on_message,
        )

        self.channel.start_consuming()
