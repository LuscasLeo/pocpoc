from contextvars import ContextVar, Token
from optparse import Option
from types import TracebackType
from typing import List, Optional, Type
from pocpoc import ClassInitializer
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.message import Message

from pocpoc.api.unit_of_work import UnitOfWork, UnitOfWorkFactory


message_dispatcher_uow_context: ContextVar[
    Optional["MessageDispatcherUnitOfWork"]
] = ContextVar("message_dispatcher_uow_context", default=None)


class MessageDispatcherUnitOfWork(UnitOfWork):
    def __init__(self, message_dispatcher: MessageDispatcher) -> None:
        self.message_dispatcher = message_dispatcher
        self.staged_messages: List[Message] = []
        self.token: Optional[Token[Optional["MessageDispatcherUnitOfWork"]]] = None

    def add_message(self, message: Message) -> None:
        self.staged_messages.append(message)

    def commit(self) -> None:
        for message in self.staged_messages:
            self.message_dispatcher.dispatch(message)

        self.staged_messages = []

    def rollback(self) -> None:
        self.staged_messages = []

    def close(self) -> None:
        self.staged_messages = []

    def __enter__(self) -> "MessageDispatcherUnitOfWork":
        self.token = message_dispatcher_uow_context.set(self)
        return self

    def __exit__(
        self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        if self.token:
            message_dispatcher_uow_context.reset(self.token)
            self.token = None

        if exc_type:
            self.rollback()

            raise exc_val

        else:
            self.commit()


class MessageDispatcherUnitOfWorkFactory(UnitOfWorkFactory):
    def __init__(self, class_initializer: ClassInitializer) -> None:
        self.class_initializer = class_initializer

    def __call__(self) -> MessageDispatcherUnitOfWork:
        return MessageDispatcherUnitOfWork(
            self.class_initializer.get_instance(MessageDispatcher)
        )


class MessageSubmitter:
    def __init__(
        self,
        message_dispatcher: MessageDispatcher,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        self.message_dispatcher = message_dispatcher
        self.uow_factory = uow_factory

    def submit(self, message: Message) -> None:
        context = message_dispatcher_uow_context.get()
        if not context:
            raise RuntimeError("No message dispatcher unit of work context")

        context.add_message(message)
