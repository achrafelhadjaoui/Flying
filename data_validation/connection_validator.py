from pydantic import BaseModel, ValidationError
from typing import Literal


class ConnectionMetadata(BaseModel):
    max_link_capacity: int | None = None


class ConnectionValidator(BaseModel):
    connection_name: Literal["connection"]
    description: list[str]
    metadata: ConnectionMetadata | None = None