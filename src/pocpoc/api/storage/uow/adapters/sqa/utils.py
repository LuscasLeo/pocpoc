from decimal import Decimal
import uuid
from typing import Any

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, TypeDecorator, DECIMAL


class GUID(TypeDecorator[UUID]):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value).hex
            else:
                # hexstring
                return value.hex

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class SafeDecimal(TypeDecorator[Decimal]):
    """Platform-independent Decimal type.

    Uses Postgresql's Decimal type, otherwise uses
    CHAR(32), decimal as string.

    """

    def __init__(self, precision: int = 8, scale: int = 2, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.precision = precision
        self.scale = scale
        self.impl_kwargs = kwargs

    impl = CHAR

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(CHAR(32))
        else:
            return dialect.type_descriptor(
                DECIMAL(self.precision, self.scale, **self.impl_kwargs)
            )

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        elif dialect.name == "sqlite":
            return str(value)
        else:
            if isinstance(value, str):
                return Decimal(value)
            elif isinstance(value, Decimal):
                return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        else:
            return Decimal(value)
