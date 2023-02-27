import json
import logging
from dataclasses import is_dataclass

from pocpoc.api.codec.json_codec import (
    LocatedValidationErrorCollection,
    decode,
    encode,
)
from pocpoc.api.messages.map import MessageMap
from pocpoc.api.messages.message import (
    Message,
    MessageMetadata,
    MessageMetadata,
)
from pocpoc.api.messages.codec import MessageDecoder, MessageEncoder

logger = logging.getLogger(__name__)


class MessageDecodeError(Exception):
    pass


class JsonMessageDecoder(MessageDecoder[bytes]):
    def __init__(self, events_map: MessageMap, encoding: str) -> None:
        self.message_map = events_map
        self.encoding = encoding

    def decode(self, message_metadata: MessageMetadata, payload: bytes) -> Message:
        message_as_dictionary = json.loads(payload.decode(self.encoding))
        assert isinstance(message_as_dictionary, dict), "Event must be a dict"

        message_type = message_metadata.message_type
        message_cls = self.message_map.get_message_type(message_type)

        if message_cls is None:
            raise MessageDecodeError(f"Message type {message_type} is not registered")

        if is_dataclass(message_cls):
            try:
                parsed_value: Message = decode(message_as_dictionary, message_cls)
                return parsed_value
            except LocatedValidationErrorCollection as e:
                logger.critical("Error deserializing Message payload: %s", e)
                raise e

        raise MessageDecodeError("Message %s is not a dataclass" % message_type)


class JsonMessageEncoder(MessageEncoder[bytes]):
    def __init__(self, encoding: str) -> None:
        self.encoding = encoding

    def encode(self, message: Message) -> bytes:
        return json.dumps(encode(message)).encode(self.encoding)
