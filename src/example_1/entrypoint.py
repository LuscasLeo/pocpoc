from example_1.message_controllers.send_email_command_controller import (
    SendEmailCommandController,
)
from example_1.message_controllers.send_email_command_controller.reset_password_rpc_controller import (
    ResetPasswordRPCController,
)
from example_1.messages import ResetPasswordRPC, SendResetPasswordEmailCommand
from pocpoc import Container


def create_container() -> Container:
    container = Container("example_1")

    container.register_message_controller(
        SendResetPasswordEmailCommand,
        SendEmailCommandController,
    ).register_rpc_controller(
        ResetPasswordRPC,
        ResetPasswordRPCController,
    )

    return container
