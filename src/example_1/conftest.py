from typing import Generator

import pytest

from example_1.entrypoint import create_container
from example_1.tests.utils import FakeMessageDispatcher, FakeMessageHandler
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.microservices import Container


@pytest.fixture(scope="session")
def container() -> Generator[Container, None, None]:
    yield create_container()


@pytest.fixture(scope="session")
def fake_dispatcher(
    container: Container,
) -> Generator[FakeMessageDispatcher, None, None]:
    dispatcher = FakeMessageDispatcher()
    container.register_service(MessageDispatcher, dispatcher)
    yield dispatcher
