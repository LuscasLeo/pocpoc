import logging
from types import TracebackType
from typing import List, Type

from pocpoc.api.unit_of_work import UnitOfWork, UnitOfWorkFactory

logger = logging.getLogger(__name__)


class AggregatedUnitOfWork(UnitOfWork):
    def __init__(self, uows: List[UnitOfWork]) -> None:
        self.uows = uows

    def commit(self) -> None:
        for uow in self.uows:
            uow.commit()

    def rollback(self) -> None:
        for uow in self.uows:
            uow.rollback()

    def close(self) -> None:
        for uow in self.uows:
            uow.close()

    def __enter__(self) -> "AggregatedUnitOfWork":
        for uow in self.uows:
            uow.__enter__()
        return self

    def __exit__(
        self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        for uow in self.uows:
            try:
                uow.__exit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                if e == exc_val:
                    continue
                else:
                    logger.critical(
                        "UnitOfWork.__exit__ raised an exception that was not the "
                        "original exception. This is a bug in the UnitOfWork "
                        "implementation. The original exception will be raised.",
                        exc_info=True,
                    )
        if exc_type:
            raise exc_val


class AggregatedUnitOfWorkFactory(UnitOfWorkFactory):
    def __init__(self, *factories: UnitOfWorkFactory) -> None:
        self.factories = [*factories]

    def __call__(self) -> UnitOfWork:
        return AggregatedUnitOfWork([factory() for factory in self.factories])
