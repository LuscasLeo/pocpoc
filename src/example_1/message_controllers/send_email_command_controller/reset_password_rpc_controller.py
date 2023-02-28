from example_1.messages import (
    ResetPasswordRequest,
    ResetPasswordResponse,
    SendResetPasswordEmailCommand,
)
from pocpoc import RPCController
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.storage.types import UnitOfWorkFactory

# UNIT OF WORK DOES NOT HAVE TO DO WITH ONLY SQL. IT CAN BE RELATED TO ANY ATOMIC OPERATION


class ResetPasswordRPCController(
    RPCController[ResetPasswordRequest, ResetPasswordResponse]
):
    def __init__(
        self, message_dispatcher: MessageDispatcher, uow_factory: UnitOfWorkFactory
    ) -> None:
        self.message_dispatcher = message_dispatcher
        self.uow_factory = uow_factory

    def execute(self, message: ResetPasswordRequest) -> ResetPasswordResponse:
        with self.uow_factory() as uow:
            self.message_dispatcher.dispatch(
                SendResetPasswordEmailCommand(message.email)
            )

            uow.commit()
            return ResetPasswordResponse(success=True)
