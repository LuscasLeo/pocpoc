from abc import ABC, abstractmethod
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Optional, Type


class EntityNotFound(Exception):
    pass


class UnitOfWork(ABC):
    @staticmethod
    def _get_context_uow() -> "UnitOfWork":
        context = ctx_var_current_uow.get()
        if context is None:
            raise RuntimeError("No context session")
        return context

    __current_ctx_token: Optional["Token[Optional[UnitOfWork]]"] = None

    def set_current_context(self) -> None:
        if self.__current_ctx_token is not None:
            raise RuntimeError("Already have a current context token")

        token = ctx_var_current_uow.set(self)
        self.__current_ctx_token = token

    def remove_current_context(self) -> None:
        if self.__current_ctx_token is None:
            raise RuntimeError("No current context token")
        ctx_var_current_uow.reset(self.__current_ctx_token)

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        return self

    @abstractmethod
    def __exit__(
        self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        raise NotImplementedError()


ctx_var_current_uow = ContextVar[Optional[UnitOfWork]]("current_uow", default=None)


class UnitOfWorkFactory(ABC):
    def __call__(self) -> UnitOfWork:
        raise NotImplementedError()
