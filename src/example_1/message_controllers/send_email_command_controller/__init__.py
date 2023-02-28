import logging
from example_1.messages import SendResetPasswordEmailCommand
from pocpoc.api.messages.controller.message_controller import MessageController

logger = logging.getLogger(__name__)

class SendEmailCommandController(MessageController[SendResetPasswordEmailCommand]):
    def execute(self, message: SendResetPasswordEmailCommand) -> None:
        logger.info("Sending email to %s", message.email)