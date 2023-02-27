import typing
from abc import ABC, abstractmethod
from typing import Generic

from pocpoc.api.messages.message import Message


RPCInput = typing.TypeVar("RPCInput")
RPCOutput = typing.TypeVar("RPCOutput", bound=Message)


class RPCBase(ABC, Generic[RPCInput, RPCOutput]):
    ...


class RPC(RPCBase[RPCInput, RPCOutput], Message):
    @abstractmethod
    def get_input(self) -> RPCInput:
        raise NotImplementedError()


class RPCClient(ABC):
    # @abstractmethod
    def submit(self, rpc: RPC[RPCInput, RPCOutput]) -> RPCOutput:
        raise NotImplementedError()


class RPCController(ABC, Generic[RPCInput, RPCOutput]):
    @abstractmethod
    def execute(self, request: RPCInput) -> RPCOutput:
        raise NotImplementedError()
