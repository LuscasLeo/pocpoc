from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pocpoc.api.di.class_initializer import ClassInitializer

ServiceT = TypeVar("ServiceT")


class DependencyInjectionManger(ClassInitializer, ABC):
    @abstractmethod
    def register(self, t: Type[ServiceT], instance: ServiceT) -> None:
        raise NotImplementedError

    @abstractmethod
    def register_async(self, t: Type[ServiceT], subtype: Type[ServiceT]) -> None:
        raise NotImplementedError
