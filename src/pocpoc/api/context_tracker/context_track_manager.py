from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Generator, Optional
from uuid import uuid4


@dataclass
class ContextTracker:
    global_started: datetime
    global_context_id: str

    local_started: datetime
    local_context_id: str
    service_name: str
    parent_context_id: Optional[str] = None


__tracker_context_var: ContextVar[Optional[ContextTracker]] = ContextVar(
    "tracker_context_var",
    default=None,
)


@contextmanager
def init_new_context(
    service_name: str,
    foregin_context: Optional[ContextTracker] = None,
) -> Generator[ContextTracker, None, None]:
    """
    Starts a context new global trace id for the current task and resets it when the task is finished.
    if foregin_context is not None, the new context will be a child of the foregin_context. Otherwise, it will be a root context.

    Usage:
        with init_new_context() as context:
            # do something

        with init_new_context(foregin_context) as context:
            # do something

    """

    new_context = ContextTracker(
        global_started=foregin_context.global_started
        if foregin_context
        else datetime.utcnow(),
        global_context_id=foregin_context.global_context_id
        if foregin_context
        else str(uuid4()),
        local_started=datetime.utcnow(),
        local_context_id=str(uuid4()),
        parent_context_id=foregin_context.local_context_id if foregin_context else None,
        service_name=service_name,
    )

    token = __tracker_context_var.set(new_context)
    try:
        yield new_context
    finally:
        __tracker_context_var.reset(token)


def get_current_context() -> Optional[ContextTracker]:
    return __tracker_context_var.get()


def inject_context(ctx: ContextTracker) -> Callable[[], None]:
    """
    Defines a new global trace id for the current task and returns a function to reset it.

    Usage:
        reset_context = inject_context(context)

        # do something

        reset_context()
    """

    token = __tracker_context_var.set(ctx)

    def __reset_context() -> None:
        __tracker_context_var.reset(token)

    return __reset_context
