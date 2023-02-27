

from json import dumps
from example_1.app import create_app
from pocpoc.api.di.adapters.custom import CustomDependencyInjectionManager
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.message import Message


class FakeMessageDispatcher(MessageDispatcher):
    def dispatch(self, event: Message) -> None:
        ...


def test_api() -> None:
    dependency_injection_manager = CustomDependencyInjectionManager()

    dependency_injection_manager.register(MessageDispatcher, FakeMessageDispatcher())

    app = create_app(dependency_injection_manager)

    test_client = app.test_client()

    response = test_client.post("/reset-password", data=dumps({"email": "ll@gg.com"}), headers={"Content-Type": "application/json"})
    response
