import random
import string
from example_1.message_controllers.password_reset_repository import (
    EmailPasswordResetRepository,
)
from example_1.messages import (
    RequestPasswordResetInput,
    RequestPasswordResetOutput,
    SendResetPasswordEmailCommand,
)
from pocpoc import RPCController
from pocpoc.api.messages.uow import MessageSubmitter
from pocpoc.api.unit_of_work import UnitOfWorkFactory

# UNIT OF WORK DOES NOT HAVE TO DO WITH ONLY SQL. IT CAN BE RELATED TO ANY ATOMIC OPERATION


class RequestPasswordResetRPCController(
    RPCController[RequestPasswordResetInput, RequestPasswordResetOutput]
):
    def __init__(
        self,
        message_submitter: MessageSubmitter,
        uow_factory: UnitOfWorkFactory,
        email_password_reset_repository: EmailPasswordResetRepository,
    ) -> None:
        self.message_submitter = message_submitter
        self.uow_factory = uow_factory
        self.email_password_reset_repository = email_password_reset_repository

    def execute(self, message: RequestPasswordResetInput) -> RequestPasswordResetOutput:
        with self.uow_factory() as uow:
            token = self.__generate_token()

            self.email_password_reset_repository.mark_pending(message.email, token)
            self.message_submitter.submit(
                SendResetPasswordEmailCommand(message.email, token)
            )

            uow.commit()
            return RequestPasswordResetOutput(success=True)

    def __generate_token(self) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=32))
