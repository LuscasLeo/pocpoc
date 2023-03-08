from json import dumps

from flask import Flask

from example_1.flask_app.app import configure_app
from example_1.messages import SendResetPasswordEmailCommand
from example_1.tests.utils import FakeMessageDispatcher
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.microservices import Container


def test_reset_password_endpoint(container: Container) -> None:
    fake_message_dispatcher = FakeMessageDispatcher()
    container.register_service(MessageDispatcher, fake_message_dispatcher)
    app = Flask(__name__)
    configure_app(app, container.get_class_initializer())

    test_client = app.test_client()

    response = test_client.post(
        "/reset-password",
        data=dumps({"email": "ll@gg.com"}),
        headers={"Content-Type": "application/json"},
    )

    assert len(fake_message_dispatcher.dispatched_messages) == 1

    assert response.status_code == 200

    assert response.json == {"success": True}


def test_incorrect_payload(container: Container) -> None:
    fake_message_dispatcher = FakeMessageDispatcher()
    container.register_service(MessageDispatcher, fake_message_dispatcher)

    app = Flask(__name__)
    configure_app(app, container.get_class_initializer())

    test_client = app.test_client()

    response = test_client.post(
        "/reset-password",
        data=dumps({}),
        headers={"Content-Type": "application/json"},
    )

    assert len(fake_message_dispatcher.dispatched_messages) == 0

    assert response.status_code == 400
