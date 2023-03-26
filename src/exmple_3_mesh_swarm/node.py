from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
import json
import random
from re import A
import string
from dataclasses import dataclass
from threading import Event, Lock
from typing import *
import traceback

from click import Option

from exmple_3_mesh_swarm.cluster import Cluster
from pocpoc.api.codec.json_codec import decode, encode

NODE_HEARTBEAT_INTERVAL = 5  # seconds
NODE_HEARTBEAT_TIMEOUT = 10  # seconds

# region message bases


@dataclass
class Request:
    """A request to the cluster."""

    request_id: str


@dataclass
class Response:
    """A response to a request."""

    request_id: str


RESPONSE_T = TypeVar("RESPONSE_T", bound=Response)
RESPONSE_HANDLER = Callable[[RESPONSE_T], None]

# endregion

# region Objects


@dataclass
class NodeState:
    """The state of a node."""

    node_id: str
    heartbeat: float
    is_master: bool


# endregion


# region Messages


@dataclass
class Heartbeat:
    """A heartbeat message."""

    node_state: NodeState


@dataclass
class ClusterStateRequest(Request):
    """A request to get the cluster state."""

    pass


@dataclass
class ClusterStateResponse(Response):
    """A response to a cluster state request."""

    nodes: Dict[str, NodeState]


@dataclass
class MasterCandidate:
    """A candidate for master."""

    node_id: str
    timestamp: float


@dataclass
class MasterVote:
    """A vote for a master candidate."""

    node_id: str


@dataclass
class MasterElected:
    """The end of a master election."""

    elected_node_id: str


# endregion

MESSAGE_MAP: Dict[str, Type[object]] = {
    Heartbeat.__name__: Heartbeat,
    ClusterStateRequest.__name__: ClusterStateRequest,
    ClusterStateResponse.__name__: ClusterStateResponse,
    MasterCandidate.__name__: MasterCandidate,
    MasterVote.__name__: MasterVote,
    MasterElected.__name__: MasterElected,
}


def gen_request_id() -> str:
    """Generate a random request id."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


@dataclass
class MessageMeta:
    node_sender: str


print_lock = Lock()

message_meta_cxtvar: ContextVar[Optional[MessageMeta]] = ContextVar(
    "message_meta_cxtvar", default=None
)


@contextmanager
def with_message_metadata(meta: MessageMeta) -> Generator[None, None, None]:
    try:
        token = message_meta_cxtvar.set(meta)
        yield
    finally:
        message_meta_cxtvar.reset(token)


def get_message_metadata() -> MessageMeta:
    """Get the node id of the current node."""
    message_meta = message_meta_cxtvar.get()
    if message_meta is None:
        raise RuntimeError("Node id not set")
    return message_meta


def fork_node(
    emit_message: Callable[[bytes], Any],
    on_message: Callable[[Callable[[bytes], Any]], Any],
    node_id: str,
    exit_event: Event,
) -> None:
    """Fork a node in a cluster."""
    # region tooling

    def println(*msg: str) -> None:
        with print_lock:
            print(
                "{}[{}] ".format(node_state.is_master and "[MASTER]" or "", node_id),
                *msg,
            )

    def broadcast(msg: object) -> None:
        """Broadcast a message to the cluster."""
        bmsg = "{} {} {}".format(
            node_id,
            msg.__class__.__name__,
            json.dumps(encode(msg)),
        ).encode("utf-8")
        emit_message(bmsg)

    def setup_message_listener(
        message_map: Dict[str, Type[object]],
        message_handler_map: Dict[Type[object], Callable[..., Any]],
    ) -> Callable[[bytes], None]:
        def on_msg(msg: bytes) -> None:
            """Handle a message received from the cluster."""

            try:
                msg_sender_id_bytes, msg_type_bytes, msg_data_bytes = msg.split(
                    b" ", maxsplit=2
                )

                msg_sender_id = msg_sender_id_bytes.decode()
                if msg_sender_id == node_id:
                    # println("Received own message: {}".format(msg.decode()))
                    return

                msg_data = msg_data_bytes.decode("utf-8")
                msg_type = msg_type_bytes.decode("utf-8")
                if msg_type in message_map:
                    msg_class = message_map[msg_type]

                    msg_data_dict = json.loads(msg_data)

                    msg_instance = decode(msg_data_dict, msg_class)

                    with with_message_metadata(MessageMeta(node_sender=msg_sender_id)):
                        if msg_class in message_handler_map:
                            message_handler_map[msg_class](msg_instance)
                else:
                    println(f"Unknown message type: {msg_type}")

            except Exception as e:
                println(f"Error while handling message: {e}", traceback.format_exc())

        return on_msg

    def handle_response(
        handler: Callable[[RESPONSE_T], None]
    ) -> Callable[[RESPONSE_T], None]:
        """Handle a response to a request."""

        def handle_response_inner(resp: RESPONSE_T) -> None:
            if resp.request_id in requests:
                requests.remove(resp.request_id)
                handler(resp)

        return handle_response_inner

    def send_request(req: Request) -> None:
        """Send a request to the cluster."""
        requests.add(req.request_id)
        broadcast(req)

    # endregion

    # region message handlers

    def on_heartbeat(hello: Heartbeat) -> None:
        """Handle a heartbeat message."""
        println(f"Node {hello.node_state.node_id} is alive")
        nodes[hello.node_state.node_id] = hello.node_state

        master = next((node for node in nodes.values() if node.is_master), None)
        if master is None:
            println("No master found, sending master candidate for {}".format(node_id))

            masters_candidates[node_state.node_id] = MasterCandidate(
                node_state.node_id, node_state.heartbeat
            )
            broadcast(MasterCandidate(node_id, node_state.heartbeat))

    def on_cluster_state_request(req: ClusterStateRequest) -> None:
        """Handle a cluster state request."""
        println(f"Received cluster state request")
        broadcast(ClusterStateResponse(req.request_id, nodes))

    @handle_response
    def on_cluster_state_response(resp: ClusterStateResponse) -> None:
        """Handle a cluster state response."""
        println(f"Received cluster state response: {resp.nodes}")

    def on_master_candidate(candidate: MasterCandidate) -> None:
        """Handle a master candidate."""
        println(f"Received master candidate: {candidate.node_id}")

        masters_candidates[candidate.node_id] = candidate

    def on_master_vote(vote: MasterVote) -> None:
        """Handle a master vote."""
        println(f"Received master vote: {vote.node_id}")
        message_meta = get_message_metadata()

        masters_candidates_votes[message_meta.node_sender] = vote.node_id

    def on_master_elected(elected: MasterElected) -> None:
        """Handle a master elected."""

        masters_candidates.clear()
        masters_candidates_votes.clear()
        if elected.elected_node_id == node_id:
            println("I am the master")
            node_state.is_master = True
            broadcast(Heartbeat(node_state))

    # endregion

    # region message handlers map

    message_handlers: Dict[Type[object], Callable[..., Any]] = {
        Heartbeat: on_heartbeat,
        ClusterStateRequest: on_cluster_state_request,
        ClusterStateResponse: on_cluster_state_response,
        MasterCandidate: on_master_candidate,
        MasterVote: on_master_vote,
        MasterElected: on_master_elected,
    }

    # endregion

    setup = setup_message_listener(
        MESSAGE_MAP,
        message_handlers,
    )

    on_message(setup)

    requests: Set[str] = set()

    node_state: NodeState = NodeState(node_id, datetime.now().timestamp(), False)

    masters_candidates: Dict[str, MasterCandidate] = {}
    masters_candidates_votes: Dict[str, str] = {}

    nodes: Dict[str, NodeState] = {node_id: node_state}

    println("Node {} started".format(node_id))

    send_request(ClusterStateRequest(gen_request_id()))

    broadcast(Heartbeat(node_state))
    while not exit_event.wait(NODE_HEARTBEAT_INTERVAL):
        now = datetime.now().timestamp()
        broadcast(Heartbeat(node_state))

        earliest_master_candidate = next(
            (
                master_candidate
                for master_candidate in masters_candidates.values()
                if master_candidate.timestamp
                == min(
                    masters_candidate.timestamp
                    for masters_candidate in masters_candidates.values()
                )
            ),
            None,
        )

        if (
            earliest_master_candidate is not None
            and now - earliest_master_candidate.timestamp > NODE_HEARTBEAT_INTERVAL
        ):
            if node_id not in masters_candidates_votes:
                random_node_id = random.choice(list(masters_candidates.keys()))

                println(
                    "Sending master vote for {} to {}".format(node_id, random_node_id)
                )

                masters_candidates_votes[node_id] = random_node_id
                broadcast(MasterVote(random_node_id))

            if len(masters_candidates_votes) == len(masters_candidates) == len(nodes):
                votes_count: Dict[str, int] = {}

                for vote in masters_candidates_votes.values():
                    if vote in votes_count:
                        votes_count[vote] += 1
                    else:
                        votes_count[vote] = 1

                votes_nodes_by_count: Dict[int, Set[str]] = {}

                for voted_node_id, vote_count in votes_count.items():
                    if vote_count in votes_nodes_by_count:
                        votes_nodes_by_count[vote_count].add(voted_node_id)
                    else:
                        votes_nodes_by_count[vote_count] = {voted_node_id}

                max_votes = max(votes_nodes_by_count.keys())
                if len(votes_nodes_by_count[max_votes]) == 1:
                    master_node_id = next(iter(votes_nodes_by_count[max_votes]))
                    println(f"New master: {master_node_id}")
                    nodes[master_node_id].is_master = True
                    broadcast(MasterElected(master_node_id))
                    broadcast(Heartbeat(node_state))
                else:
                    println(
                        "There was a tie: {} ({} vote(s))".format(
                            votes_nodes_by_count[max_votes], max_votes
                        )
                    )

                masters_candidates.clear()
                masters_candidates_votes.clear()

    println("Node {} stopped".format(node_id))
