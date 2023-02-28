import logging
from example_1.message_controllers.send_email_command_controller import (
    SendEmailCommandController,
)
from example_1.message_controllers.reset_password_rpc_controller import (
    ResetPasswordRPCController,
)
from example_1.messages import ResetPasswordRPC, SendResetPasswordEmailCommand
from pocpoc import Container
from pocpoc.api.messages.adapters.runtime.runtime_message_dispatcher import (
    RuntimeMessageDispatcher,
)
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.message import Message
from pocpoc.api.messages.uow import MessageDispatcherUnitOfWorkFactory
from pocpoc.api.storage.uow.adapters.sqa.sqa_storage import SQAAUnitOfWork
from pocpoc.api.unit_of_work import UnitOfWorkFactory
from pocpoc.api.unit_of_work.aggregated import AggregatedUnitOfWorkFactory


logger = logging.getLogger(__name__)

def create_container() -> Container:
    container = Container("example_1")

    def handle_message_dispatch(message: Message) -> None:
        message_type = container._message_controller_map.get_message_type(
            message.message_type()
        )

        if message_type is None:
            logger
            return

        message_controllers = (
            container._message_controller_map.message_controller_map.get(message_type)
        )

        if message_controllers is None:
            raise Exception(
                f"Message controller not found for message type {message_type}"
            )

        for message_controller in message_controllers:
            instance = container.get_class_initializer().get_instance(
                message_controller
            )

            instance.execute(message)

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
    ).register_service(
        MessageDispatcher, RuntimeMessageDispatcher(handle_message_dispatch)
    )

    return container
