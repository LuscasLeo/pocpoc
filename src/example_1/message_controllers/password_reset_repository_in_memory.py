from typing import Set

from example_1.message_controllers.domain import Token
from example_1.message_controllers.password_reset_repository import (
    EmailPasswordResetRepository,
)


class TokenNotFound(Exception):
    pass


class InMemoryEmailPasswordResetRepository(EmailPasswordResetRepository):
    def __init__(self) -> None:
        self.tokens: Set[Token] = set()

    def mark_sent(self, email: str) -> None:
        ...

    def mark_pending(self, email: str, token: str) -> None:
        self.tokens.add(Token(email, token))

    def get_token(self, token: str) -> Token:
        token_item = next((t for t in self.tokens if t.token == token), None)
        if token_item is None:
            raise TokenNotFound()

        return token_item

    def mark_done(self, token: str) -> None:
        ...
