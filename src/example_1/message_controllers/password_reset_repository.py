from example_1.message_controllers.domain import Token


class EmailPasswordResetRepository:
    def mark_sent(self, email: str) -> None:
        ...

    def mark_pending(self, email: str, token: str) -> None:
        ...

    def get_token(self, token: str) -> Token:
        ...

    def mark_done(self, token: str) -> None:
        ...
