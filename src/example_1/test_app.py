from json import dumps
from typing import List
from example_1.app import create_app
from pocpoc.api.di.adapters.custom import CustomDependencyInjectionManager
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.message import Message
from example_1.messages import SendResetPasswordEmailCommand


class FakeMessageDispatcher(MessageDispatcher):
    def __init__(self) -> None:
        self.dispatched_messages: List[Message] = []

    def dispatch(self, event: Message) -> None:
        self.dispatched_messages.append(event)


def test_api() -> None:
    dependency_injection_manager = CustomDependencyInjectionManager()

    fake_message_dispatcher = FakeMessageDispatcher()
    dependency_injection_manager.register(MessageDispatcher, fake_message_dispatcher)

    app = create_app(dependency_injection_manager)

    test_client = app.test_client()

    response = test_client.post(
        "/reset-password",
        data=dumps({"email": "ll@gg.com"}),
        headers={"Content-Type": "application/json"},
    )

    assert len(fake_message_dispatcher.dispatched_messages) == 1

    assert (
        SendResetPasswordEmailCommand(email="ll@gg.com")
        in fake_message_dispatcher.dispatched_messages
    )

    assert response.status_code == 200

    assert response.json == {"message": "Password reset"}
