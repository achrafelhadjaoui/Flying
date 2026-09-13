from pydantic import BaseModel

from .zone_validator import ZoneValidator
from .connection_validator import ConnectionValidator


class ConfigValidator(BaseModel):
    nb_drones: int
    zones: list[ZoneValidator]
    connections: list[ConnectionValidator]
    # connections: list[ConnectionValidator]