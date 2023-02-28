from example_1.message_controllers.send_email_command_controller import (
    SendEmailCommandController,
)
from example_1.message_controllers.reset_password_rpc_controller import (
    ResetPasswordRPCController,
)
from example_1.messages import ResetPasswordRPC, SendResetPasswordEmailCommand
from pocpoc import Container
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.uow import MessageDispatcherUnitOfWorkFactory
from pocpoc.api.storage.uow.adapters.sqa.sqa_storage import SQAAUnitOfWork
from pocpoc.api.unit_of_work import UnitOfWorkFactory
from pocpoc.api.unit_of_work.aggregated import AggregatedUnitOfWorkFactory


def create_container() -> Container:
    container = Container("example_1")

    container.register_message_controller(
        SendResetPasswordEmailCommand,
        SendEmailCommandController,
    ).register_rpc_controller(
        ResetPasswordRPC,
        ResetPasswordRPCController,
    ).register_service(
        UnitOfWorkFactory,
        AggregatedUnitOfWorkFactory(
            # SQAAUnitOfWork(
            #     None
            # ),
            MessageDispatcherUnitOfWorkFactory(container.get_class_initializer()),
        ),
    )

    return container
