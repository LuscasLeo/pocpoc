from functools import wraps
from types import TracebackType
from typing import Any, Callable, Type, TypeVar

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session, sessionmaker

from pocpoc.api.storage.types import (
    EntityNotFound,
    UnitOfWork,
    UnitOfWorkFactory,
)

T = TypeVar("T")


def raises_not_found(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except EntityNotFound:
            raise
        except NoResultFound:
            raise EntityNotFound()

    return wrapper


def current_session() -> Session:
    return SQAAUnitOfWork.get_current_session()


class SQAAUnitOfWork(UnitOfWork):
    @staticmethod
    def get_sqa_current_uow() -> "SQAAUnitOfWork":
        context = UnitOfWork._get_context_uow()
        if not isinstance(context, SQAAUnitOfWork):
            raise RuntimeError("Context session is not a SQAAUnitOfWork")
        return context

    @staticmethod
    def get_current_session() -> Session:
        return SQAAUnitOfWork.get_sqa_current_uow().session

    @property
    def session(self) -> Session:
        if not self._session:
            raise RuntimeError("No session")
        return self._session

    _session: Session

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SQAAUnitOfWork":
        self.set_current_context()
        self._session: Session = self._session_factory()
        return self

    def __exit__(
        self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        self.remove_current_context()

        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
        if exc_type is not None:
            raise exc_val.with_traceback(exc_tb)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def close(self) -> None:
        return self.session.close()


class SQAUOWFactory(UnitOfWorkFactory):
    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory

    def __call__(self) -> SQAAUnitOfWork:
        return SQAAUnitOfWork(session_factory=self.session_factory)
