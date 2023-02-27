from dataclasses import dataclass
from typing import Any, Callable, Type, TypeVar

from flask import Flask, Response, jsonify, make_response, request

from pocpoc import ClassInitializer
from pocpoc.api.codec.json_codec import decode
from pocpoc.api.messages.dispatcher import MessageDispatcher
from pocpoc.api.messages.message import Message

T = TypeVar("T")
V = TypeVar("V")


def request_body(model: Type[T]) -> Callable[[Callable[..., V]], Callable[..., V]]:
    def decorator(func: Callable[..., V]) -> Callable[..., V]:
        def wrapper(*args: Any, **kwargs: Any) -> V:
            json_body = request.get_json(silent=True)
            if json_body is None:
                return jsonify({"message": "Invalid JSON"}), 400  # type: ignore

            body = decode(json_body, model)
            return func(*args, **{**kwargs, "body": body})

        return wrapper

    return decorator


@dataclass
class ResetPasswordModel:
    email: str
    """
    Email of the user, used to send the reset password email
    """


@dataclass(unsafe_hash=True)
class SendResetPasswordEmailModel(Message):
    @classmethod
    def message_type(cls) -> str:
        return "example_1.commands.send_reset_password_email"

    email: str
    """
    Email of the user, used to send the reset password email
    """


def create_app(class_initializer: ClassInitializer) -> Flask:
    app = Flask(__name__)

    message_dispatcher = class_initializer.get_instance(MessageDispatcher)

    @request_body(ResetPasswordModel)
    def reset_password(body: ResetPasswordModel) -> Response:
        message_dispatcher.dispatch(SendResetPasswordEmailModel(email=body.email))

        return jsonify({"message": "Password reset"})

    app.add_url_rule(
        "/reset-password", "reset_password", reset_password, methods=["POST"]
    )

    return app
