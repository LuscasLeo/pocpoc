import logging
from typing import Iterable, Type

from pika.adapters.blocking_connection import BlockingChannel
from pika.exchange_type import ExchangeType
from pocpoc.api.messages.message import Message

logger = logging.getLogger(__name__)


def register_messages_as_exchange_to_queue(
    messages: Iterable[Type[Message]],
    service_queue: str,
    channel: BlockingChannel,
) -> None:
    # declare a queue
    channel.queue_declare(queue=service_queue, durable=True)

    # for each event type, declare a exchange and bind to the queue
    for message_cls in messages:
        logger.debug(
            "Declaring exchange %s and binding to queue %s",
            message_cls.message_type(),
            service_queue,
        )

        channel.exchange_declare(
            exchange=message_cls.message_type(),
            exchange_type=ExchangeType.fanout,
            durable=True,
        )
        channel.queue_bind(
            queue=service_queue,
            exchange=message_cls.message_type(),
        )
