from types import TracebackType
from typing import List, Type

from pocpoc.api.unit_of_work import UnitOfWork, UnitOfWorkFactory


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
            uow.__exit__(exc_type, exc_val, exc_tb)


class AggregatedUnitOfWorkFactory(UnitOfWorkFactory):
    def __init__(self, *factories: UnitOfWorkFactory) -> None:
        self.factories = [*factories]

    def __call__(self) -> UnitOfWork:
        return AggregatedUnitOfWork([factory() for factory in self.factories])
