"""Abstract description of a zone of the network."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractZone(ABC):
    """A class that represents a zone model.

    It holds everything a zone read from a map file carries, and
    leaves to its children the job of linking the zone to its
    neighbours.
    """

    def __init__(self, zone_name: str, name: str, x_coordinate: int,
                 y_coordinate: int, color: str = "", capacity: int = 1,
                 zone_type: str = "normal") -> None:
        """Init function to initialise the given needed data.

        Args:
            zone_name (str): the prefix of the line, for instance
                'hub' or 'start_hub'.
            name (str): the name of the zone.
            x_coordinate (int): the x coordinate of the zone.
            y_coordinate (int): the y coordinate of the zone.
            color (str): the colour asked in the map file.
            capacity (int): how many drones the zone may hold.
            zone_type (str): normal, blocked, restricted or priority.
        """
        self.zone_name = zone_name
        self.name = name
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.color = color
        self.capacity = capacity
        self.zone_type = zone_type
        self.connections: list[list[Any]] = []

    @abstractmethod
    def connect_connection(self, data: dict[str, Any]) -> None:
        """Extract every connection the zone takes part in.

        Args:
            data (dict[str, Any]): the parsed content of the map file.
        """
        pass
