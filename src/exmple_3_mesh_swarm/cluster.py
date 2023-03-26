from dataclasses import dataclass
from queue import Queue
from threading import Event, Thread
from typing import *


class Cluster:
    def __init__(self) -> None:
        self.listeners: List[Callable[[bytes], Iterable[bytes]]] = []

        self.message_queue: Queue[bytes] = Queue()

    def broadcast(self, msg: bytes) -> None:
        """Broadcast a message to all nodes in the cluster."""
        self.message_queue.put(msg)

        while not self.message_queue.empty():
            message = self.message_queue.get()
            for listener in self.listeners:
                new_messages = listener(message)
                for new_message in new_messages:
                    self.message_queue.put(new_message)


@dataclass
class NodeThread:
    node_id: str
    thread: Thread
    exit_event: Event
