from typing import Any, Dict

from pocpoc.api.codec.json_codec import encode
from pocpoc.api.logging.json_logging_formatter import JsonLoggingAddon
from pocpoc.api.context_tracker.context_track_manager import (
    get_current_context,
)


class ContextTrackerLoggingAddon(JsonLoggingAddon):
    def handle(self, record: Dict[str, Any]) -> None:
        current_context = get_current_context()
        if current_context is not None:
            record.update(encode(current_context))
