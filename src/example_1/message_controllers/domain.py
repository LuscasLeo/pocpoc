from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    email: str
    token: str
