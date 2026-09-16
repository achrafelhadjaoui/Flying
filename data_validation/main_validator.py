"""Schema of a whole map file."""

from pydantic import BaseModel, PositiveInt

from .zone_validator import ZoneValidator
from .connection_validator import ConnectionValidator


class ConfigValidator(BaseModel):
    """Everything the parser read from one map file."""

    nb_drones: PositiveInt
    zones: list[ZoneValidator]
    connections: list[ConnectionValidator]
