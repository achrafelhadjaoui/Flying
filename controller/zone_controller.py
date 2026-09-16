from typing import Any

from model import Zone


class ZoneController(Zone):
    """Zone creation, responsible for a zone and its connections."""

    def __init__(self, zone_name: str, name: str, x_coordinate: int,
                 y_coordinate: int, color: str = "", max_drones: int = 1,
                 zone: str = "normal") -> None:
        """Init function to initialise the given needed data.

        Args:
            zone_name (str): the prefix of the line, for instance
                'hub' or 'start_hub'.
            name (str): the name of the zone.
            x_coordinate (int): the x coordinate of the zone.
            y_coordinate (int): the y coordinate of the zone.
            color (str): the colour asked in the map file.
            max_drones (int): how many drones the zone may hold.
            zone (str): normal, blocked, restricted or priority.
        """
        super().__init__(
            zone_name,
            name,
            x_coordinate,
            y_coordinate,
            color,
            max_drones,
            zone,
        )

    # assign connection to the zone
    def connect_connection(self, data: dict[str, Any]) -> None:
        """Connect the zone with the connections it appears in.

        Every neighbour is stored as [neighbour name, link capacity]
        directly inside the parsed data, so the pathfinding and the
        simulation can walk the graph without searching again.

        Args:
            data (dict[str, Any]): the parsed content of the map file.
        """
        neighbors_data: list[list[Any]] = []

        for connection in data["connections"]:
            data_list: list[Any] = []

            if self.name not in connection["description"]:
                continue

            for zone in connection["description"]:
                if zone != self.name:
                    data_list.append(zone)

            link_capacity = connection["metadata"].get(
                "max_link_capacity",
                1,
            )
            data_list.append(link_capacity)

            neighbors_data.append(data_list)

        self.connections = neighbors_data
        data["zones"][Zone.index]["neighbors"] = neighbors_data
        Zone.index += 1
