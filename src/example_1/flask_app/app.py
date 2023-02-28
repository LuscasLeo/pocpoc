from typing import Any, Callable, Type, TypeVar

from flask import Flask, Response, jsonify, request

from example_1.message_controllers.send_email_command_controller.reset_password_rpc_controller import (
    ResetPasswordRPCController,
)
from example_1.messages import ResetPasswordRequest
from pocpoc import ClassInitializer
from pocpoc.api.codec.json_codec import LocatedValidationErrorCollection, decode, encode

T = TypeVar("T")
V = TypeVar("V")


def request_body(model: Type[T]) -> Callable[[Callable[..., V]], Callable[..., V]]:
    def decorator(func: Callable[..., V]) -> Callable[..., V]:
        def wrapper(*args: Any, **kwargs: Any) -> V:
            json_body = request.get_json(silent=True)
            if json_body is None:
                return jsonify({"message": "Invalid JSON"}), 400  # type: ignore
            try: 
                body = decode(json_body, model)
            except LocatedValidationErrorCollection as e:
                return jsonify({"message": "Invalid Body", "errors": encode(e.errors)}), 400  # type: ignore
            return func(*args, **{**kwargs, "body": body})

        return wrapper

    return decorator


def create_app(class_initializer: ClassInitializer) -> Flask:
    app = Flask(__name__)

    reset_password_rpc_controller = class_initializer.get_instance(
        ResetPasswordRPCController
    )

    @request_body(ResetPasswordRequest)
    def reset_password(body: ResetPasswordRequest) -> Response:
        resp = reset_password_rpc_controller.execute(body)

        return jsonify(encode(resp))

    app.add_url_rule(
        "/reset-password", "reset_password", reset_password, methods=["POST"]
    )

    return app


# region IN BRAINSTORMING MODE

# class HTTPRPCMapper:
#     def __init__(self) -> None:
#         self._rpcs: Dict[str, Dict[str, Type[RPC[Any, Any]]]] = {}
#         self._controllers: Dict[str, Dict[str, Type[RPCController[Any, Any]]]] = {}

#     def get_controller(self, path: str, method: str) -> Type[RPCController[RPCInput, RPCOutput]]:
#         return self._controllers[path][method]

#     def register(
#         self,
#         path: str,
#         method: str,
#         rpc: Type[RPC[RPCInput, RPCOutput]],
#         controller: Type[RPCController[RPCInput, RPCOutput]],
#     ) -> None:
#         if path not in self._rpcs:
#             self._rpcs[path] = {}
#         self._rpcs[path][method] = rpc

#         if path not in self._controllers:
#             self._controllers[path] = {}
#         self._controllers[path][method] = controller


# http_rpc_mapper = HTTPRPCMapper()

# http_rpc_mapper.register(
#     "/reset-password",
#     "POST",
#     ResetPasswordRPC,
#     ResetPasswordRPCController,
# )


# class HTTPRPCClient(RPCClient):
#     def submit(self, rpc: RPC[RPCInput, RPCOutput]) -> RPCOutput:
#         return super().submit(rpc)


# class RPCDecoder:

#     def decode(self, data: Dict[str, Any], model: Type[T]) -> T:
#         return decode(data, model)

# class FlaskRPCClient(RPCMessageHandler):

#     def __init__(self, rpc_decoder: RPCDecoder, http_rpc_mapper: HTTPRPCMapper, class_initializer: ClassInitializer) -> None:
#         self._rpc_decoder = rpc_decoder
#         self._http_rpc_mapper = http_rpc_mapper
#         self._class_initializer = class_initializer

#     def setup(self, flask_app: Flask, http_rpc_mapper: HTTPRPCMapper) -> None:

#         for path, methods in http_rpc_mapper._rpcs.items():
#             for method, rpc in methods.items():
#                 flask_app.add_url_rule(
#                     path, f"{path}-{method}", self._handle_rpc(rpc, path, method), methods=[method]
#                 )

#     def _handle_rpc(self, rpc: Type[RPC[RPCInput, RPCOutput]], path: str, method: str) -> Callable[..., RPCOutput]:
#         def decorator(*args: Any, **kwargs: Any) -> RPCOutput:
#             json_body = request.get_json(silent=True)
#             if json_body is None:
#                 return jsonify({"message": "Invalid JSON"}), 400

#             body = self._rpc_decoder.decode(json_body, rpc.get_input_type())

#             controller_instance = self.class_initializer ## UNFINISHED


#     def handle_message(self, message_data: MessageMetadata, message: Message) -> None:
#         return super().handle_message(message_data, message)


# endregion
