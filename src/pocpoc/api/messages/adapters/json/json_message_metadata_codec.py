import json

from pocpoc.api.codec.json_codec import decode, encode
from pocpoc.api.messages.codec import (
    MessageMetadataDecoder,
    MessageMetadataEncoder,
)
from pocpoc.api.messages.message import MessageMetadata


class JsonMessageMetadataEncoder(MessageMetadataEncoder[bytes]):
    def __init__(
        self,
        encoding: str,
    ):
        self.encoding = encoding

    def encode(self, metadata: MessageMetadata) -> bytes:
        return json.dumps(encode(metadata)).encode(self.encoding)


class JsonMessageMetadataDecoder(MessageMetadataDecoder[bytes]):
    def __init__(
        self,
        encoding: str,
    ):
        self.encoding = encoding

    def decode(self, message: bytes) -> MessageMetadata:
        return decode(json.loads(message.decode(self.encoding)), MessageMetadata)
