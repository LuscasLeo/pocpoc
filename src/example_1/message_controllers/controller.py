import logging
from example_1.message_controllers.password_reset_repository import (
    EmailPasswordResetRepository,
)
from example_1.messages import SendResetPasswordEmailCommand
from pocpoc.api.messages.controller.message_controller import MessageController
from typing_extensions import Protocol

from pocpoc.api.unit_of_work import UnitOfWorkFactory


logger = logging.getLogger(__name__)


class SendResetPasswordEmailCommandController(
    MessageController[SendResetPasswordEmailCommand]
):
    def __init__(
        self,
        email_password_reset_repository: EmailPasswordResetRepository,
        unit_of_work_factory: UnitOfWorkFactory,
    ):
        self.email_password_reset_repository = email_password_reset_repository
        self.unit_of_work_factory = unit_of_work_factory

    def execute(self, message: SendResetPasswordEmailCommand) -> None:
        with self.unit_of_work_factory() as uow:
            logger.info(
                "Sending email to  %s with token %s",
                message.email,
                message.token,
            )
            self.email_password_reset_repository.mark_sent(message.email)
            uow.commit()
