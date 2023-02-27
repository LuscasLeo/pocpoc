from abc import ABC, abstractmethod
from typing import Generic, Tuple, TypeVar

from pocpoc.api.messages.message import Message, MessageMetadata

T = TypeVar("T")


class MessageEncoder(ABC, Generic[T]):
    @abstractmethod
    def encode(self, message: Message) -> T:
        raise NotImplementedError()


class MessageDecoder(ABC, Generic[T]):
    @abstractmethod
    def decode(self, message_medatada: MessageMetadata, payload: T) -> Message:
        raise NotImplementedError()


class MessageMetadataEncoder(ABC, Generic[T]):
    @abstractmethod
    def encode(self, message: MessageMetadata) -> T:
        raise NotImplementedError()


class MessageMetadataDecoder(ABC, Generic[T]):
    @abstractmethod
    def decode(self, message: T) -> MessageMetadata:
        raise NotImplementedError()


class MessageKitEncoder(ABC, Generic[T]):
    @abstractmethod
    def encode(self, message_metadata: MessageMetadata, message: Message) -> T:
        raise NotImplementedError()


class MessageKitDecoder(ABC, Generic[T]):
    @abstractmethod
    def decode(self, payload: T) -> Tuple[MessageMetadata, Message]:
        raise NotImplementedError()
