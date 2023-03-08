import logging
from example_1.messages import PasswordResetSuccessEvent
from pocpoc import MessageController

logger = logging.getLogger(__name__)


class PasswordResetSuccessEventController(MessageController[PasswordResetSuccessEvent]):
    def execute(self, message: PasswordResetSuccessEvent) -> None:
        logger.warning(f"Password reset success for user {message.email}")
