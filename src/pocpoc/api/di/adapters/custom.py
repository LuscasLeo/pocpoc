import inspect
import logging
from typing import Any, Dict, Type, cast

from pocpoc.api.di import DependencyInjectionManger, ServiceT
from pocpoc.api.di.class_initializer import InitializerType

logger = logging.getLogger(__name__)


class CustomDependencyInjectionManager(DependencyInjectionManger):
    def __init__(self) -> None:
        self.cached_dependencies: Dict[Type[Any], Any] = {}
        self.cached_subtypes: Dict[Type[Any], Type[Any]] = {}

    def get_instance(self, type_: Type[InitializerType]) -> InitializerType:
        return cast(InitializerType, self.__get_or_create_instance(type_))

    def __get_or_create_instance(self, type_: Type[Any]) -> Any:
        if type_ in self.cached_dependencies:
            logger.debug(
                "Using cached instance of type {} for type {}".format(
                    self.cached_dependencies[type_].__class__.__name__, type_.__name__
                )
            )
            return self.cached_dependencies[type_]
        elif type_ in self.cached_subtypes:
            logger.debug(
                "Creating instance for type {} using subtype {}".format(
                    type_.__name__, self.cached_subtypes[type_].__name__
                )
            )
            new_instance = self.__create_instance(self.cached_subtypes[type_])
            self.register(type_, new_instance)
            return new_instance

        logger.debug("Creating instance for type {}".format(type_.__name__))
        new_instance = self.__create_instance(type_)
        self.register(type_, new_instance)
        return new_instance

    def __create_instance(self, type_: Type[Any]) -> Any:
        try:
            constructor = type_.__init__

            parameters = inspect.signature(constructor).parameters
            args = {
                name: self.__get_or_create_instance(parameter.annotation)
                for name, parameter in parameters.items()
                if parameter.annotation != inspect.Parameter.empty
            }
            return type_(**args)
        except Exception:
            logger.critical(
                "Failed to inject dependencies for type {}".format(type_.__name__),
                exc_info=True,
            )

    def register(self, t: Type[ServiceT], instance: ServiceT) -> None:
        self.cached_dependencies[t] = instance

    def register_async(self, t: Type[ServiceT], subtype: Type[ServiceT]) -> None:
        self.cached_subtypes[t] = subtype
