from dataclasses import dataclass

from pocpoc.api.messages.message import Message


@dataclass
class RPCServerErrorResponse(Message):
    message: str

    @classmethod
    def message_type(cls) -> str:
        return "rpc_server_error_response"


class RPCServerError(Exception):
    def __init__(self, error_response: RPCServerErrorResponse) -> None:
        self.error_response = error_response
