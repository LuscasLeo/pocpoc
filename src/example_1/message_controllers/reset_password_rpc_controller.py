from abc import ABC, abstractmethod
import logging
from typing_extensions import Protocol
from example_1.message_controllers.password_reset_repository import (
    EmailPasswordResetRepository,
)
from example_1.message_controllers.password_reset_repository_in_memory import (
    TokenNotFound,
)
from example_1.messages import (
    PasswordResetSuccessEvent,
    ResetPasswordInput,
    ResetPasswordOutput,
)
from pocpoc import RPCController
from pocpoc.api.messages.uow import MessageSubmitter
from pocpoc.api.unit_of_work import UnitOfWorkFactory


logger = logging.getLogger(__name__)


class InvalidTokenException(Exception):
    pass


class TokenExpired(Exception):
    pass


class User(Protocol):
    email: str


class ResetPasswordRPCController(
    RPCController[ResetPasswordInput, ResetPasswordOutput]
):
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        email_password_reset_repository: EmailPasswordResetRepository,
        message_submitter: MessageSubmitter,
    ) -> None:
        self.unit_of_work_factory = uow_factory
        self.email_password_reset_repository = email_password_reset_repository
        self.message_submitter = message_submitter

    def execute(self, request: ResetPasswordInput) -> ResetPasswordOutput:
        try:
            with self.unit_of_work_factory() as uow:
                token = self.email_password_reset_repository.get_token(request.token)
                self.email_password_reset_repository.mark_done(request.token)

                self.message_submitter.submit(
                    PasswordResetSuccessEvent(email=token.email)
                )

                uow.commit()

                return ResetPasswordOutput(success=True)

        except (TokenNotFound, TokenExpired):
            raise InvalidTokenException()
