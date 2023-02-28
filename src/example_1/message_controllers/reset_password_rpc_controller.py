from example_1.messages import (
    ResetPasswordRequest,
    ResetPasswordResponse,
    SendResetPasswordEmailCommand,
)
from pocpoc import RPCController
from pocpoc.api.messages.uow import MessageSubmitter
from pocpoc.api.unit_of_work import UnitOfWorkFactory

# UNIT OF WORK DOES NOT HAVE TO DO WITH ONLY SQL. IT CAN BE RELATED TO ANY ATOMIC OPERATION


class ResetPasswordRPCController(
    RPCController[ResetPasswordRequest, ResetPasswordResponse]
):
    def __init__(
        self, message_submitter: MessageSubmitter, uow_factory: UnitOfWorkFactory
    ) -> None:
        self.message_submitter = message_submitter
        self.uow_factory = uow_factory

    def execute(self, message: ResetPasswordRequest) -> ResetPasswordResponse:
        with self.uow_factory() as uow:
            self.message_submitter.submit(SendResetPasswordEmailCommand(message.email))

            uow.commit()
            return ResetPasswordResponse(success=True)
