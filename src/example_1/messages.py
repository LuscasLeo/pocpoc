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

    token: str
    """
    Token used to reset the password
    """


@dataclass(unsafe_hash=True)
class RequestPasswordResetInput:
    email: str


@dataclass(unsafe_hash=True)
class RequestPasswordResetOutput(Message):
    @classmethod
    def message_type(cls) -> str:
        return "example_1.rpc.request_password_reset.output"

    success: bool


@dataclass(unsafe_hash=True)
class RequestPasswordResetRPC(
    RPC[RequestPasswordResetInput, RequestPasswordResetOutput]
):
    input: RequestPasswordResetInput

    @classmethod
    def message_type(cls) -> str:
        return "example_1.rpc.request_password_reset"

    def get_input(self) -> RequestPasswordResetInput:
        return self.input


@dataclass(unsafe_hash=True)
class ResetPasswordInput:
    token: str
    password: str


@dataclass(unsafe_hash=True)
class ResetPasswordOutput(Message):
    @classmethod
    def message_type(cls) -> str:
        return "example_1.rpc.reset_password.output"

    success: bool


@dataclass(unsafe_hash=True)
class ResetPasswordRPC(RPC[ResetPasswordInput, ResetPasswordOutput]):
    input: ResetPasswordInput

    @classmethod
    def message_type(cls) -> str:
        return "example_1.rpc.reset_password"

    def get_input(self) -> ResetPasswordInput:
        return self.input


@dataclass(unsafe_hash=True)
class PasswordResetSuccessEvent(Message):
    @classmethod
    def message_type(cls) -> str:
        return "example_1.events.password_reset_success"

    email: str
    """
    Email of the user, used to send the reset password email
    """
