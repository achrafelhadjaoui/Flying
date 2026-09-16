"""Entry point: read a map, find a route and fly the drones on it."""

import sys
from typing import Any

from controller import validate_data
from controller.logic_handling import ShortPath
from controller.simulation import Simulation
from controller import ZoneController
from parsing import Parser
from vue import SimulationView

ZoneData = dict[str, Any]


def read_map(file_path: str) -> Parser:
    """Read and check the whole map file.

    Args:
        file_path (str): path of the map file to read.

    Returns:
        Parser: the parser holding the validated data.
    """
    file = Parser()
    file.file_check(file_path)
    file.first_line_check()
    file.zone_check()
    file.connection_check()
    validate_data(file.data)

    return file


def build_zones(data: dict[str, Any]) -> None:
    """Create one controller per zone and link it to its neighbours.

    Args:
        data (dict[str, Any]): the parsed content of the map file.
    """
    for zone_data in data["zones"]:
        metadata = zone_data["metadata"]
        zone_controller = ZoneController(
            zone_data["zone_name"],
            zone_data["name"],
            zone_data["x_coordinate"],
            zone_data["y_coordinate"],
            metadata.get("color", ""),
            int(metadata.get("max_drones", 1)),
            metadata.get("zone", "normal"),
        )
        zone_controller.connect_connection(data)


def find_hubs(data: dict[str, Any]) -> tuple[ZoneData, ZoneData]:
    """Pick the start zone and the end zone out of the map.

    Args:
        data (dict[str, Any]): the parsed content of the map file.

    Returns:
        tuple[ZoneData, ZoneData]: the start zone and the end zone.
    """
    start_zone: ZoneData | None = None
    end_zone: ZoneData | None = None

    for zone in data["zones"]:
        if zone["zone_name"] == "start_hub":
            start_zone = zone
        elif zone["zone_name"] == "end_hub":
            end_zone = zone

    if start_zone is None or end_zone is None:
        raise ValueError("the map needs a start_hub and an end_hub")

    return (start_zone, end_zone)


def fly(data: dict[str, Any], route: list[str]) -> None:
    """Fly the whole fleet along a route and show every turn.

    Args:
        data (dict[str, Any]): the parsed content of the map file.
        route (list[str]): the zone names, from the start to the end.
    """
    nb_drones = data["nb_drones"]
    simulation = Simulation(data["zones"], route, nb_drones)
    view = SimulationView(data["zones"], nb_drones)

    for moves, occupancy in simulation.run():
        view.add_turn(moves, occupancy)

    view.show()

    if simulation.deadlock:
        print("\nthe drones are stuck, no move is possible any more")


def main() -> None:
    """Read the map given on the command line and run the simulation."""
    if len(sys.argv) != 2:
        print("enter path of file")
        sys.exit(3)

    try:
        file = read_map(sys.argv[1])

        # creating instances from the zone_controller to connect the
        # zones with the connections
        build_zones(file.data)

        # finding the shortest path between the start and the end zone
        start_zone, end_zone = find_hubs(file.data)

        short_path = ShortPath(start_zone, end_zone, file.data["zones"])
        short_path.find_shortest_path()

        if not short_path.path:
            print("no route found between the start and the end zone")
            return

        route = " -> ".join(str(zone["name"]) for zone in short_path.path)
        print(f"shortest path: {route}")
        print(f"cost: {short_path.total_cost} turns\n")

        fly(file.data, [str(zone["name"]) for zone in short_path.path])

    except Exception as e:
        print(str(e))
        sys.exit(3)


if __name__ == "__main__":
    main()
