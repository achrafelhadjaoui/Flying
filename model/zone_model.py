from .abstract_classes import AbstractZone


class Zone(AbstractZone):
    """A class that represents a zone model."""

    # class index for tracking the current zone in the data
    index: int = 0

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
