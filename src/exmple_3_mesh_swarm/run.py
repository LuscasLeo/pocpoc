from contextvars import ContextVar
import crypt
import random
import string
from threading import Event, Thread
from typing import *

from exmple_3_mesh_swarm.cluster import Cluster, NodeThread
from exmple_3_mesh_swarm.node import fork_node
from redis import Redis

message_emitter_ctxvr: ContextVar[Optional[Callable[[bytes], None]]] = ContextVar(
    "message_emitter_ctxvr", default=None
)

if __name__ == "__main__":
    # cluster = Cluster()
    redis = Redis(
        host="localhost",
        port=6379,
        db=0,
    )

    pubsub = redis.pubsub()
    pubsub.subscribe("mesh")

    nodes_thread: Dict[str, NodeThread] = {}

    def add_node() -> None:
        node_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        exit_event = Event()

        def emit_msg(msg: bytes) -> None:
            message_emitter = message_emitter_ctxvr.get()
            if message_emitter is not None:
                message_emitter(msg)
            else:
                redis.publish("mesh", msg)

        def on_new_msg(callback: Callable[[bytes], None]) -> None:
            def setup_message(msg: bytes) -> List[bytes]:
                new_messages: List[bytes] = []

                def message_emitter(msg: bytes) -> None:
                    new_messages.append(msg)

                token = message_emitter_ctxvr.set(message_emitter)
                try:
                    callback(msg)
                finally:
                    message_emitter_ctxvr.reset(token)

                return new_messages

            # region Redis Integration
            def start_listening() -> None:
                for msg in pubsub.listen():  # type: ignore
                    if msg["type"] == "message":
                        new_messages = setup_message(msg["data"])
                        for new_msg in new_messages:
                            redis.publish("mesh", new_msg)

            Thread(
                target=start_listening, daemon=True, name=f"Node_{node_id}_listener"
            ).start()
            # endregion
            # cluster.listeners.append(setup_message)

        th = Thread(
            target=fork_node,
            args=(emit_msg, on_new_msg, node_id, exit_event),
            daemon=True,
            name=f"Node_{node_id}_main",
        )
        th.start()
        nodes_thread[node_id] = NodeThread(node_id, th, exit_event)

    for a in range(1):
        add_node()

    while True:
        print("Enter a message to broadcast:")
        msg = input()

        spl = msg.split(" ")

        if spl[0] == "add":
            add_node()

        elif spl[0] == "remove":
            if len(spl) == 1:
                print("Please specify a node id to remove")
            else:
                node_id = spl[1]
                if node_id in nodes_thread:
                    nodes_thread[node_id].exit_event.set()
                    del nodes_thread[node_id]
                else:
                    print(f"Node {node_id} not found")

        elif spl[0] == "list":
            print("Nodes:")
            for node_id in nodes_thread:
                print(f" - {node_id}")
