from enum import Enum

from pydantic import BaseModel


class ZoneNames(str, Enum):
    start_hub = "start_hub"
    hub = "hub"
    end_hub = "end_hub"


class ZoneType(str, Enum):
    priority = "priority"
    restricted = "restricted"
    
class Color(str, Enum):
    red = "red"
    blue = "blue"
    green = "green"
    yellow = "yellow"
    orange = "orange"
    cyan = "cyan"


class Metadata(BaseModel):
    color: Color | None = None
    max_drones: int | None = None
    zone_type: ZoneType | None = None


class ZoneValidator(BaseModel):
    zone_name: ZoneNames
    name: str
    x_coordinate: int
    y_coordinate: int
    metadata: Metadata