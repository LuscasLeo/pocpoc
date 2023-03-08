from typing import Generator

import pytest

from example_1.entrypoint import (
    create_container,
    create_message_dispatcher_uow,
    register_aggregated_uow_hooks,
    register_runtime_message_dispatcher,
)
from example_1.tests.utils import FakeMessageDispatcher, FakeMessageHandler
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.microservices import Container
from pocpoc.api.utils.debugging import setup_debug_logging

setup_debug_logging("example.*")


@pytest.fixture(scope="session")
def container() -> Generator[Container, None, None]:
    container = create_container()
    register_runtime_message_dispatcher(container)
    register_aggregated_uow_hooks(container, create_message_dispatcher_uow)
    yield container


@pytest.fixture(scope="session")
def fake_dispatcher(
    container: Container,
) -> Generator[FakeMessageDispatcher, None, None]:
    dispatcher = FakeMessageDispatcher()
    container.register_service(MessageDispatcher, dispatcher)
    yield dispatcher
