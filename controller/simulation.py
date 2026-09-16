"""Turn by turn scheduling of the drones along a route.

This first version sends the whole fleet down the single route found
by the A* search. It already respects every rule of the subject, but
it does not spread the drones over several routes yet.
"""

from typing import Any

from vue import Move

ZoneData = dict[str, Any]

# what one turn produces: the moves, then who stands where
TurnRecord = tuple[list[Move], dict[str, list[str]]]


class Simulation:
    """Play the flight turn after turn.

    The rules enforced here are the ones of VII.2 and VII.3:

    * a zone holds at most max_drones drones, the start and the end
      zones being the two exceptions,
    * a connection is used by at most max_link_capacity drones during
      the same turn,
    * a drone leaving a zone frees its place for the same turn,
    * entering a restricted zone takes two turns, the drone spending
      the first one on the connection and landing on the second one.
    """

    RESTRICTED: str = "restricted"

    def __init__(self, zones: list[ZoneData], path: list[str],
                 nb_drones: int) -> None:
        """Prepare the fleet on the start zone.

        Args:
            zones (list[ZoneData]): every zone of the network.
            path (list[str]): the route, from the start to the end.
            nb_drones (int): how many drones have to be delivered.
        """
        by_name = {str(zone["name"]): zone for zone in zones}

        self.zones = zones
        self.path: list[ZoneData] = [by_name[name] for name in path]
        self.nb_drones = nb_drones
        self.last: int = len(self.path) - 1

        # drone -> index on the route
        self.position: dict[str, int] = {}
        # drone -> (index left behind, index it must land on)
        self.flying: dict[str, tuple[int, int]] = {}
        self.delivered: set[str] = set()
        self.deadlock: bool = False

        # how many drones stand on each step of the route, a drone in
        # the air already counting on the step it will land on
        self.occupied: list[int] = [0] * len(self.path)
        self.occupied[0] = nb_drones

        for number in range(1, nb_drones + 1):
            self.position[f"D{number}"] = 0

    def read_number(self, value: Any, fallback: int = 1) -> int:
        """Read a capacity written either as a text or as a number.

        The parser keeps the metadata as written in the file, so a
        capacity may arrive as the string "2" instead of the number 2.

        Args:
            value (Any): the value found in the metadata.
            fallback (int): what to return when the value is unusable.

        Returns:
            int: the capacity, never below one.
        """
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return fallback

    def zone_capacity(self, index: int) -> int:
        """Return how many drones a step of the route can hold.

        Args:
            index (int): the position on the route.

        Returns:
            int: the capacity, the whole fleet for the two hubs.
        """
        zone = self.path[index]

        if str(zone["zone_name"]) in ("start_hub", "end_hub"):
            return self.nb_drones

        metadata = zone.get("metadata", {})

        return self.read_number(metadata.get("max_drones", 1))

    def link_capacity(self, index: int) -> int:
        """Return how many drones may fly one connection at once.

        Args:
            index (int): the step the connection starts from.

        Returns:
            int: the capacity of the connection.
        """
        zone = self.path[index]
        target = str(self.path[index + 1]["name"])

        for neighbor in zone.get("neighbors", []):
            if len(neighbor) < 2 or str(neighbor[0]) != target:
                continue

            return self.read_number(neighbor[1])

        return 1

    def is_restricted(self, index: int) -> bool:
        """Tell whether reaching a step costs two turns.

        Args:
            index (int): the position on the route.

        Returns:
            bool: True when the zone is restricted.
        """
        metadata = self.path[index].get("metadata", {})

        return str(metadata.get("zone", "normal")) == self.RESTRICTED

    def connection_name(self, index: int) -> str:
        """Return the name of the connection leaving a step.

        Args:
            index (int): the step the connection starts from.

        Returns:
            str: the connection written as "zone1-zone2".
        """
        return (
            f"{self.path[index]['name']}-{self.path[index + 1]['name']}"
        )

    def land_flying(self) -> list[Move]:
        """Land every drone that spent the previous turn in the air.

        The subject forbids waiting on a connection, so the place was
        already booked when the flight started and the landing can
        never fail.

        Returns:
            list[Move]: the landings of this turn.
        """
        moves: list[Move] = []
        flights = sorted(self.flying.items(), key=lambda pair: -pair[1][1])

        for drone, (origin, target) in flights:
            del self.flying[drone]

            name = str(self.path[target]["name"])
            arrived = target == self.last

            moves.append(Move.arrival(
                drone, str(self.path[origin]["name"]), name, arrived
            ))

            if arrived:
                self.delivered.add(drone)
            else:
                self.position[drone] = target

        return moves

    def advance(self, landed: set[str]) -> list[Move]:
        """Try to move every drone one step further.

        Drones are handled from the one closest to the goal, so a drone
        that leaves a zone frees the place for the one behind it during
        the very same turn.

        Args:
            landed (set[str]): the drones that just came down from a
                connection this very turn. Reaching a restricted zone
                costs two turns, so their move is already done and
                they must not fly again before the next turn.

        Returns:
            list[Move]: the moves and the waits of this turn.
        """
        moves: list[Move] = []
        used: dict[int, int] = {}
        order = sorted(self.position, key=lambda one: -self.position[one])

        for drone in order:
            if drone in landed:
                continue

            index = self.position[drone]
            step = index + 1
            here = str(self.path[index]["name"])

            room = self.occupied[step] < self.zone_capacity(step)
            free = used.get(index, 0) < self.link_capacity(index)

            if not room or not free:
                moves.append(Move.wait(drone, here))
                continue

            used[index] = used.get(index, 0) + 1
            self.occupied[index] -= 1
            self.occupied[step] += 1

            if self.is_restricted(step):
                # the place on the restricted zone is booked now, so
                # the drone is sure to land on the next turn
                del self.position[drone]
                self.flying[drone] = (index, step)
                moves.append(Move.flight(
                    drone, here, self.connection_name(index)
                ))
                continue

            name = str(self.path[step]["name"])
            arrived = step == self.last

            moves.append(Move.arrival(drone, here, name, arrived))

            if arrived:
                del self.position[drone]
                self.delivered.add(drone)
            else:
                self.position[drone] = step

        return moves

    def occupancy(self) -> dict[str, list[str]]:
        """Return which drones stand on which zone.

        Returns:
            dict[str, list[str]]: zone name -> drone identifiers.
        """
        standing: dict[str, list[str]] = {}

        for drone, index in self.position.items():
            standing.setdefault(
                str(self.path[index]["name"]), []
            ).append(drone)

        for drone in self.delivered:
            standing.setdefault(
                str(self.path[self.last]["name"]), []
            ).append(drone)

        return standing

    def play_turn(self) -> list[Move]:
        """Play one whole turn.

        Returns:
            list[Move]: everything that happened during the turn.
        """
        moves = self.land_flying()
        landed = {move.drone for move in moves}
        moves.extend(self.advance(landed))

        return moves

    def finished(self) -> bool:
        """Tell whether every drone reached the end zone.

        Returns:
            bool: True when the simulation is over.
        """
        return len(self.delivered) >= self.nb_drones

    def run(self, max_turns: int = 0) -> list[TurnRecord]:
        """Play the whole flight.

        Args:
            max_turns (int): safety limit, computed from the fleet and
                the route when it is left to zero.

        Returns:
            list[TurnRecord]: one (moves, occupancy) pair
            per turn.
        """
        if self.last < 1 or self.nb_drones < 1:
            return []

        if max_turns <= 0:
            max_turns = (self.nb_drones + 2) * (self.last + 2)

        turns: list[TurnRecord] = []

        while not self.finished() and len(turns) < max_turns:
            moves = self.play_turn()
            turns.append((moves, self.occupancy()))

            moving = [one for one in moves if one.kind != Move.WAIT]

            if not moving and not self.flying:
                # nobody can move any more, stop instead of looping
                self.deadlock = True
                break

        return turns
