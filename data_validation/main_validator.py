from pydantic import BaseModel

from .zone_validator import ZoneValidator


class ConfigValidator(BaseModel):
    nb_drones: int
    zones: list[ZoneValidator]
    # connections: list[ConnectionValidator]