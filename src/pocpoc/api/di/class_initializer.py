from abc import ABCMeta
from typing import Type, TypeVar

InitializerType = TypeVar("InitializerType")


class ClassInitializer(metaclass=ABCMeta):
    # @abstractmethod
    def get_instance(self, type_: Type[InitializerType]) -> InitializerType:
        raise NotImplementedError()
