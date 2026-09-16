from enum import Enum

from pydantic import BaseModel, PositiveInt


class ZoneNames(str, Enum):
    """The three prefixes a zone line may start with."""

    start_hub = "start_hub"
    hub = "hub"
    end_hub = "end_hub"


class ZoneType(str, Enum):
    """The four zone types the subject allows."""

    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class Metadata(BaseModel):
    """The optional tags written between the square brackets.

    The subject sets no list of allowed colours, any single word is
    accepted, so the colour is kept as a plain string.
    """

    color: str | None = None
    max_drones: PositiveInt | None = None
    zone: ZoneType | None = None


class ZoneValidator(BaseModel):
    """One zone, as the parser stored it."""

    zone_name: ZoneNames
    name: str
    x_coordinate: int
    y_coordinate: int
    metadata: Metadata
