from typing import Any, Callable, Type, TypeVar

from flask import Flask, Response, jsonify, make_response, request

from example_1.message_controllers.request_password_reset_rpc_controller import (
    RequestPasswordResetRPCController,
)
from example_1.message_controllers.reset_password_rpc_controller import (
    InvalidTokenException,
    ResetPasswordRPCController,
    TokenNotFound,
)
from example_1.messages import (
    RequestPasswordResetInput,
    ResetPasswordInput,
    ResetPasswordOutput,
)
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


def configure_app(app: Flask, class_initializer: ClassInitializer) -> None:
    request_password_reset_rpc_controller = class_initializer.get_instance(
        RequestPasswordResetRPCController
    )

    @request_body(RequestPasswordResetInput)
    def request_password_reset(body: RequestPasswordResetInput) -> Response:
        resp = request_password_reset_rpc_controller.execute(body)

        return jsonify(encode(resp))

    app.add_url_rule(
        "/reset-password", "reset_password", request_password_reset, methods=["POST"]
    )

    reset_passwoord_rpc_controller = class_initializer.get_instance(
        ResetPasswordRPCController
    )

    @request_body(ResetPasswordInput)
    def reset_password(body: ResetPasswordInput) -> Response:
        try:
            resp = reset_passwoord_rpc_controller.execute(body)

            return jsonify(encode(resp))
        except InvalidTokenException:
            return make_response(jsonify({"message": "Invalid Token"}), 400)

    app.add_url_rule(
        "/reset-password/confirm",
        "reset_password_confirm",
        reset_password,
        methods=["POST"],
    )
