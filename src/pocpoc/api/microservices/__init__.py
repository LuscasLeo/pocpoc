from abc import ABC, abstractmethod
from contextvars import ContextVar
import logging
import signal
from contextlib import contextmanager
from threading import Lock, Thread
from typing import Any, Callable, Generator, List, Optional, Type


from pocpoc.api.di import DependencyInjectionManger, ServiceT
from pocpoc.api.di.adapters.custom import (
    CustomDependencyInjectionManager,
)
from pocpoc.api.di.class_initializer import ClassInitializer
from pocpoc.api.messages.events.event_controller import (
    EventController,
    MessageT,
)
from pocpoc.api.messages.events.event_map import EventMap
from pocpoc.api.messages.map import MessageMap
from pocpoc.api.messages.rpc import (
    RPC,
    RPCController,
    RPCInput,
    RPCOutput,
)
from pocpoc.api.messages.rpc.errors import RPCServerErrorResponse
from pocpoc.api.messages.rpc.map import RPCMap

logger = logging.getLogger(__name__)

lock_context_var = ContextVar("lock_context_var", default=False)


class GracefulKiller:
    __kill_now = False
    __stop_consumer_thread: Optional[Thread] = None
    __on_exit_callbacks: List[Callable[[], None]] = []
    lock: Lock = Lock()

    @staticmethod
    def setup() -> None:
        signal.signal(signal.SIGINT, GracefulKiller.exit_gracefully)
        signal.signal(signal.SIGTERM, GracefulKiller.exit_gracefully)

    @staticmethod
    def on_exit(callback: Callable[[], None]) -> None:
        GracefulKiller.__on_exit_callbacks.append(callback)

    @staticmethod
    def exit_gracefully(signum: int, frame: Any) -> None:
        logger.warning("Received signal %s", signum)
        if GracefulKiller.__kill_now:
            logger.warning("Received signal %s again, exiting", signum)
            exit(1)
        GracefulKiller.__kill_now = True

        def execute_close() -> None:
            with GracefulKiller.lock:
                for callback in GracefulKiller.__on_exit_callbacks:
                    callback()

        if GracefulKiller.__stop_consumer_thread is None:
            GracefulKiller.__stop_consumer_thread = Thread(
                target=execute_close, daemon=True
            )
            GracefulKiller.__stop_consumer_thread.start()

    @staticmethod
    @contextmanager
    def wait_for_kill() -> Generator[None, None, None]:
        if lock_context_var.get():
            raise RuntimeError("Cannot nest wait_for_kill")
        token = lock_context_var.set(True)
        with GracefulKiller.lock:
            try:
                yield
            except KeyboardInterrupt:
                GracefulKiller.__kill_now = True
                raise
            finally:
                lock_context_var.reset(token)

    @staticmethod
    def should_continue() -> bool:
        return not GracefulKiller.__kill_now


class Container:
    def __init__(self, service_name: str) -> None:
        self._service_name = service_name
        self._message_map = MessageMap()
        self._rpc_map = RPCMap()
        self._event_map = EventMap()
        self._dependency_injection_manager: DependencyInjectionManger = (
            CustomDependencyInjectionManager()
        )

        self.register_service(ClassInitializer, self._dependency_injection_manager)
        self._message_map.register_messages(RPCServerErrorResponse)

    def get_message_map(self) -> MessageMap:
        return self._message_map

    def register_messages_types(self, *message_types: Type[MessageT]) -> "Container":
        self._message_map.register_messages(*message_types)
        return self

    def register_rpc_controller(
        self,
        message_type: Type[RPC[RPCInput, RPCOutput]],
        controller_type: Type[RPCController[RPCInput, RPCOutput]],
    ) -> "Container":
        self._rpc_map.register(message_type, controller_type)
        self._message_map.register_messages(message_type)
        return self

    def register_event_controller(
        self,
        message_type: Type[MessageT],
        *controller_type: Type[EventController[MessageT]]
    ) -> "Container":
        self._event_map.register(message_type, *controller_type)
        self._message_map.register_messages(message_type)
        return self

    def register_event_hook(
        self, message_type: Type[MessageT], controller_type: Callable[[MessageT], None]
    ) -> "Container":
        self._event_map.register_hook(message_type, controller_type)
        self._message_map.register_messages(message_type)
        return self

    def register_service(
        self, service_type: Type[ServiceT], service: ServiceT
    ) -> "Container":
        self._dependency_injection_manager.register(service_type, service)
        return self

    def register_service_async(
        self, service_type: Type[ServiceT], service: Type[ServiceT]
    ) -> "Container":
        self._dependency_injection_manager.register_async(service_type, service)
        return self

    def get_class_initializer(self) -> ClassInitializer:
        return self._dependency_injection_manager


class ContainerHandler(ABC):
    def __init__(self) -> None:
        self.pre_start_hooks: List[Callable[[Container], None]] = []
        self.container: Optional[Container] = None

    @abstractmethod
    def _run(self, container: Container) -> None:
        raise NotImplementedError()

    def set_container(self, container: Container) -> "ContainerHandler":
        self.container = container
        return self

    def run(self) -> None:
        if self.container is None:
            raise ValueError("Container not set")

        for hook in self.pre_start_hooks:
            hook(self.container)

        self._run(self.container)

    def before_start(self, *hooks: Callable[[Container], None]) -> "ContainerHandler":
        self.pre_start_hooks.extend(hooks)
        return self
