from typing import Literal

from pydantic import BaseModel, PositiveInt


class ConnectionMetadata(BaseModel):
    """The optional tag written between the square brackets."""

    max_link_capacity: PositiveInt | None = None


class ConnectionValidator(BaseModel):
    """One connection, as the parser stored it."""

    connection_name: Literal["connection"]
    description: list[str]
    metadata: ConnectionMetadata | None = None
