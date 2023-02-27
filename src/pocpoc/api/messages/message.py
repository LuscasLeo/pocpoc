from abc import ABC, ABCMeta, abstractclassmethod, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pocpoc.api.context_tracker.context_track_manager import (
    ContextTracker,
)


class Message(ABC):
    @classmethod
    @abstractmethod
    def message_type(cls) -> str:
        raise NotImplementedError(
            "message_type() not implemented for class {}".format(cls.__name__)
        )


@dataclass
class MessageMetadata:
    message_type: str
    sent_at: datetime
    tracked_context: Optional[ContextTracker]
