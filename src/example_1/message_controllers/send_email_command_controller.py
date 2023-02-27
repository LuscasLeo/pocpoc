from example_1.messages import SendResetPasswordEmailCommand
from pocpoc.api.messages.controller.message_controller import MessageController


class SendEmailCommandController(MessageController[SendResetPasswordEmailCommand]):
    def execute(self, message: SendResetPasswordEmailCommand) -> None:
        return super().execute(message)
