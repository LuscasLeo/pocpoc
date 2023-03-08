import logging
from typing import Callable, List
from example_1.message_controllers.password_reset_repository import (
    EmailPasswordResetRepository,
)
from example_1.message_controllers.password_reset_repository_in_memory import (
    InMemoryEmailPasswordResetRepository,
)
from example_1.message_controllers.reset_password_rpc_controller import (
    ResetPasswordRPCController,
)
from example_1.message_controllers.send_email_command_controller import (
    SendResetPasswordEmailCommandController,
)
from example_1.message_controllers.request_password_reset_rpc_controller import (
    RequestPasswordResetRPCController,
)
from example_1.messages import (
    PasswordResetSuccessEvent,
    RequestPasswordResetRPC,
    ResetPasswordRPC,
    SendResetPasswordEmailCommand,
)
from pocpoc import Container
from pocpoc.api.messages.adapters.runtime.runtime_message_dispatcher import (
    RuntimeMessageDispatcher,
)
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.message import Message
from pocpoc.api.messages.uow import MessageDispatcherUnitOfWorkFactory
from pocpoc.api.unit_of_work import UnitOfWorkFactory
from pocpoc.api.unit_of_work.aggregated import AggregatedUnitOfWorkFactory


logger = logging.getLogger(__name__)


def create_container() -> Container:
    container = Container("example_1")

    container.register_message_controller(
        SendResetPasswordEmailCommand,
        SendResetPasswordEmailCommandController,
    ).register_rpc_controller(
        RequestPasswordResetRPC,
        RequestPasswordResetRPCController,
    ).register_service(
        ResetPasswordRPC,
        ResetPasswordRPCController,
    ).register_service_async(
        EmailPasswordResetRepository, InMemoryEmailPasswordResetRepository
    )

    return container


def register_runtime_message_dispatcher(container: Container) -> None:
    def handle_message_dispatch(message: Message) -> None:
        message_type = container._message_controller_map.get_message_type(
            message.message_type()
        )

        if message_type is None:
            logger.warning(
                f"Message type {message.message_type()} not found in message controller map"
            )
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

    container.register_service(
        MessageDispatcher, RuntimeMessageDispatcher(handle_message_dispatch)
    )


def register_aggregated_uow_hooks(
    container: Container, *callables: Callable[[Container], UnitOfWorkFactory]
) -> None:
    container.register_service(
        UnitOfWorkFactory,
        AggregatedUnitOfWorkFactory(*[callable(container) for callable in callables]),
    )


def create_message_dispatcher_uow(
    container: Container,
) -> MessageDispatcherUnitOfWorkFactory:
    return MessageDispatcherUnitOfWorkFactory(container.get_class_initializer())
