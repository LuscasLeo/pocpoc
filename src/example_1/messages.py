from dataclasses import dataclass

from pocpoc.api.messages.message import Message
from pocpoc.api.messages.rpc import RPC


@dataclass(unsafe_hash=True)
class SendResetPasswordEmailCommand(Message):
    @classmethod
    def message_type(cls) -> str:
        return "example_1.commands.send_reset_password_email"

    email: str
    """
    Email of the user, used to send the reset password email
    """


@dataclass(unsafe_hash=True)
class ResetPasswordRequest:
    email: str


@dataclass(unsafe_hash=True)
class ResetPasswordResponse(Message):
    @classmethod
    def message_type(cls) -> str:
        return "example_1.rpc.reset_password.response"

    success: bool


@dataclass(unsafe_hash=True)
class ResetPasswordRPC(RPC[ResetPasswordRequest, ResetPasswordResponse]):
    input: ResetPasswordRequest

    @classmethod
    def message_type(cls) -> str:
        return "example_1.rpc.reset_password"

    def get_input(self) -> ResetPasswordRequest:
        return self.input
