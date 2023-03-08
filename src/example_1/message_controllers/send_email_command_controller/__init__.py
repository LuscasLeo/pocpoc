import logging
from example_1.message_controllers.password_reset_repository import (
    EmailPasswordResetRepository,
)
from example_1.messages import SendResetPasswordEmailCommand
from pocpoc.api.messages.controller.message_controller import MessageController
from typing_extensions import Protocol


logger = logging.getLogger(__name__)


class SendResetPasswordEmailCommandController(
    MessageController[SendResetPasswordEmailCommand]
):
    def __init__(self, email_password_reset_repository: EmailPasswordResetRepository):
        ...

    def execute(self, message: SendResetPasswordEmailCommand) -> None:
        logger.info("Sending email to %s with token %s", message.email, message.token)
