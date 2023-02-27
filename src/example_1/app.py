from dataclasses import dataclass
from typing import Any, Callable, Type, TypeVar

from flask import Flask, Response, jsonify, make_response, request

from pocpoc import ClassInitializer
from pocpoc.api.codec.json_codec import decode
from pocpoc.api.messages.dispatcher import MessageDispatcher


@dataclass
class ResetPasswordModel:
    email: str
    """
    Email of the user, used to send the reset password email
    """


T = TypeVar("T")
V = TypeVar("V")


def request_body(model: Type[T]) -> Callable[[Callable[..., V]], Callable[..., V]]:
    def decorator(func: Callable[..., V]) -> Callable[..., V]:
        def wrapper(*args: Any, **kwargs: Any) -> V:
            json_body = request.json
            if json_body is None:
                return make_response("Invalid request", 400)  # type: ignore

            body = decode(json_body, model)
            return func(*args, **{**kwargs, "body": body})

        return wrapper

    return decorator


def create_app(class_initializer: ClassInitializer) -> Flask:
    app = Flask(__name__)

    message_dispatcher = class_initializer.get_instance(MessageDispatcher)

    @request_body(ResetPasswordModel)
    def reset_password(body: ResetPasswordModel) -> Response:
        # do something
        return jsonify({"message": "Password reset"})

    app.add_url_rule(
        "/reset-password", "reset_password", reset_password, methods=["POST"]
    )

    return app
