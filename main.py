import sys
from typing import Any

from controller import validate_data
from controller import ZoneController
from controller.logic_handling import ShortPath
from controller.simulation import Simulation
from parsing import Parser
from vue import SimulationView


ZoneData = dict[str, Any]


class FlyIn:
    """Main application controller for the Fly-in simulation."""

    def __init__(self, file_path: str) -> None:
        """Initialize the application.

        Args:
            file_path (str): path to the map file.
        """
        self.file_path = file_path
        self.file: Parser | None = None

    def read_map(self) -> Parser:
        """Read and validate the whole map file.

        Returns:
            Parser: parser containing the validated map data.
        """
        file = Parser()
        file.file_check(self.file_path)
        file.first_line_check()
        file.zone_check()
        file.connection_check()
        validate_data(file.data)

        self.file = file
        return file

    def build_zones(self, data: dict[str, Any]) -> None:
        """Create and connect a controller for every zone.

        Args:
            data (dict[str, Any]): parsed map data.
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

    def find_hubs(
        self,
        data: dict[str, Any],
    ) -> tuple[ZoneData, ZoneData]:
        """Find the start and end hubs.

        Args:
            data (dict[str, Any]): parsed map data.

        Returns:
            tuple[ZoneData, ZoneData]: start and end zones.
        """
        start_zone: ZoneData | None = None
        end_zone: ZoneData | None = None

        for zone in data["zones"]:
            if zone["zone_name"] == "start_hub":
                start_zone = zone
            elif zone["zone_name"] == "end_hub":
                end_zone = zone

        if start_zone is None or end_zone is None:
            raise ValueError(
                "the map needs a start_hub and an end_hub"
            )

        return start_zone, end_zone

    def find_route(
        self,
        start_zone: ZoneData,
        end_zone: ZoneData,
        zones: list[ZoneData],
    ) -> list[ZoneData]:
        """Find the shortest route between the two hubs.

        Args:
            start_zone (ZoneData): starting zone.
            end_zone (ZoneData): destination zone.
            zones (list[ZoneData]): all zones in the map.

        Returns:
            list[ZoneData]: zones forming the shortest route.
        """
        short_path = ShortPath(start_zone, end_zone, zones)
        short_path.find_shortest_path()

        if not short_path.path:
            print(
                "no route found between the start and the end zone"
            )
            return []

        route = " -> ".join(
            str(zone["name"]) for zone in short_path.path
        )
        print(f"shortest path: {route}")
        print(f"cost: {short_path.total_cost} turns\n")

        return short_path.path

    def fly(
        self,
        data: dict[str, Any],
        route: list[str],
    ) -> None:
        """Run the drone simulation and display every turn.

        Args:
            data (dict[str, Any]): parsed map data.
            route (list[str]): zone names forming the route.
        """
        nb_drones = data["nb_drones"]
        simulation = Simulation(data["zones"], route, nb_drones)
        view = SimulationView(data["zones"], nb_drones)

        for moves, occupancy in simulation.run():
            view.add_turn(moves, occupancy)

        view.show()

        if simulation.deadlock:
            print(
                "\nthe drones are stuck, "
                "no move is possible any more"
            )

    def run(self) -> None:
        """Run the complete Fly-in application."""
        file = self.read_map()
        self.build_zones(file.data)

        start_zone, end_zone = self.find_hubs(file.data)

        path = self.find_route(
            start_zone,
            end_zone,
            file.data["zones"],
        )

        if not path:
            return

        route = [str(zone["name"]) for zone in path]
        self.fly(file.data, route)


def main() -> None:
    """Start the Fly-in application."""
    if len(sys.argv) != 2:
        print("enter path of file")
        sys.exit(3)

    try:
        app = FlyIn(sys.argv[1])
        app.run()
    except Exception as e:
        print(str(e))
        sys.exit(3)


if __name__ == "__main__":
    main()
