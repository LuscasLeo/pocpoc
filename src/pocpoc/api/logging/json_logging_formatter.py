import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pythonjsonlogger.jsonlogger import JsonFormatter  # type: ignore


class JsonLoggingAddon(ABC):
    @abstractmethod
    def handle(self, record: Dict[str, Any]) -> None:
        pass


class JsonLoggingFormatter(JsonFormatter):  # type: ignore
    addons: List[JsonLoggingAddon] = []

    def add_addon(self, addon: JsonLoggingAddon) -> None:
        self.addons.append(addon)

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        for addon in self.addons:
            addon.handle(log_record)
