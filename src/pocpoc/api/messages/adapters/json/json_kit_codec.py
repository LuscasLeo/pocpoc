from typing import Tuple
from pocpoc.api.messages.codec import (
    MessageDecoder,
    MessageEncoder,
    MessageKitDecoder,
    MessageKitEncoder,
    MessageMetadataDecoder,
    MessageMetadataEncoder,
)
from pocpoc.api.messages.message import Message, MessageMetadata


class BufferWriter:
    def __init__(self) -> None:
        self.buffer = bytearray()

    def write_int(self, value: int) -> None:
        self.write(value.to_bytes(4, "big"))

    def write_string(self, value: str, encoding: str = "utf-8") -> None:
        self.write_int(len(value))
        self.write(value.encode(encoding))

    def write_bytes(self, value: bytes) -> None:
        self.write_int(len(value))
        self.write(value)

    def write(self, data: bytes) -> None:
        self.buffer.extend(data)

    def getvalue(self) -> bytes:
        return bytes(self.buffer)


class BufferReader:
    def __init__(self, buffer: bytes) -> None:
        self.buffer = buffer
        self.offset = 0

    def read(self, size: int) -> bytes:
        data = self.buffer[self.offset : self.offset + size]
        self.offset += size
        return data

    def read_int(self) -> int:
        return int.from_bytes(self.read(4), "big")

    def read_string(self, encoding: str = "utf-8") -> str:
        size = self.read_int()
        return self.read(size).decode(encoding)

    def read_bytes(self) -> bytes:
        size = self.read_int()
        return self.read(size)


class JsonMessageKitEncoder(MessageKitEncoder[bytes]):
    def __init__(
        self,
        json_message_metadata_encoder: MessageMetadataEncoder[bytes],
        json_message_encoder: MessageEncoder[bytes],
    ) -> None:
        self.json_message_metadata_encoder = json_message_metadata_encoder
        self.json_message_encoder = json_message_encoder

    def encode(self, message_metadata: MessageMetadata, message: Message) -> bytes:
        buffer_writer = BufferWriter()
        buffer_writer.write_bytes(
            self.json_message_metadata_encoder.encode(message_metadata)
        )
        buffer_writer.write_bytes(self.json_message_encoder.encode(message))
        return buffer_writer.getvalue()


class JsonMessageKitDecoder(MessageKitDecoder[bytes]):
    def __init__(
        self,
        json_message_metadata_decoder: MessageMetadataDecoder[bytes],
        json_message_decoder: MessageDecoder[bytes],
    ) -> None:
        self.json_message_metadata_decoder = json_message_metadata_decoder
        self.json_message_decoder = json_message_decoder

    def decode(self, message_buffer: bytes) -> Tuple[MessageMetadata, Message]:
        buffer_reader = BufferReader(message_buffer)

        message_metadata_bytes = buffer_reader.read_bytes()
        message_bytes = buffer_reader.read_bytes()

        message_metadata = self.json_message_metadata_decoder.decode(
            message_metadata_bytes
        )

        message = self.json_message_decoder.decode(message_metadata, message_bytes)

        return message_metadata, message
