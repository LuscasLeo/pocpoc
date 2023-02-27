import logging
from typing import Any, Dict, Optional, Type
from pocpoc.api.messages.map import MessageMap

from pocpoc.api.messages.rpc import (
    RPC,
    RPCController,
    RPCInput,
    RPCOutput,
)

logger = logging.getLogger(__name__)


class RPCMap(MessageMap):
    def __init__(self) -> None:
        super().__init__()
        self.rpc_controller_map: Dict[
            Type[RPC[Any, Any]], Type[RPCController[Any, Any]]
        ] = {}
        self.rpc_controller_map_by_name: Dict[str, Type[RPCController[Any, Any]]] = {}
        self.rpc_type_by_name: Dict[str, Type[RPC[Any, Any]]] = {}

    def register(
        self,
        rpc_type: Type[RPC[RPCInput, RPCOutput]],
        handler: Type[RPCController[RPCInput, RPCOutput]],
    ) -> None:
        super().register_messages(rpc_type)

        if rpc_type in self.rpc_controller_map:
            logger.warning(
                f"RPC type {rpc_type} already registered, replacing with {handler.__module__}.{handler.__name__}"
            )

        self.rpc_controller_map[rpc_type] = handler

        logger.debug(
            f"Registered RPC type {rpc_type.message_type()} with handler {handler.__module__}.{handler.__name__}"
        )

        self.rpc_controller_map_by_name[rpc_type.message_type()] = handler
        self.rpc_type_by_name[rpc_type.message_type()] = rpc_type

    def get_controller_by_name(
        self, rpc_type: str
    ) -> Optional[Type[RPCController[Any, Any]]]:
        return self.rpc_controller_map_by_name.get(rpc_type)
