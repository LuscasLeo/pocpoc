from dataclasses import dataclass

from pocpoc.api.messages.message import Message


@dataclass(unsafe_hash=True)
class SendResetPasswordEmailCommand(Message):
    @classmethod
    def message_type(cls) -> str:
        return "example_1.commands.send_reset_password_email"

    email: str
    """
    Email of the user, used to send the reset password email
    """
