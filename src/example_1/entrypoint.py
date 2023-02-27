from example_1.message_controllers.send_email_command_controller import (
    SendEmailCommandController,
)
from example_1.messages import SendResetPasswordEmailCommand
from pocpoc import Container

container = Container("example_1")

container.register_message_controller(
    SendResetPasswordEmailCommand, SendEmailCommandController
)
