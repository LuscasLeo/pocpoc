from example_1.messages import SendResetPasswordEmailCommand
from example_1.test_app import FakeMessageDispatcher


def test_send_email_command_controller(fake_dispatcher: FakeMessageDispatcher) -> None:
    fake_dispatcher.dispatch(SendResetPasswordEmailCommand("asdasdasd"))
