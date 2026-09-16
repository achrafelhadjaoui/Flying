from typing import Any

from vue import Move

ZoneData = dict[str, Any]

# what one turn produces: the moves, then who stands where
TurnRecord = tuple[list[Move], dict[str, list[str]]]


class Simulation:
    """Play the flight turn after turn.

    Every drone carries its own route, so the fleet may be spread over
    as many paths as the map allows. The zones and the connections are
    therefore counted by name and not by step, since two routes often
    share a piece of the network.

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

    HUBS: tuple[str, ...] = ("start_hub", "end_hub")

    def __init__(self, zones: list[ZoneData],
                 routes: dict[str, list[str]], nb_drones: int) -> None:
        """Prepare the fleet on the start zone.

        Args:
            zones (list[ZoneData]): every zone of the network.
            routes (dict[str, list[str]]): drone -> the zone names of
                the route it was given, from the start to the end.
            nb_drones (int): how many drones have to be delivered.
        """
        self.zones = zones
        self.by_name: dict[str, ZoneData] = {
            str(zone["name"]): zone for zone in zones
        }
        self.routes = routes
        self.nb_drones = nb_drones

        # drone -> how far it went on its own route, a drone in the
        # air already counting on the step it will land on
        self.step: dict[str, int] = {}
        # drone -> (zone left behind, connection it flies over)
        self.flying: dict[str, tuple[str, str]] = {}
        self.delivered: set[str] = set()
        self.deadlock: bool = False

        # zone name -> how many drones stand there or booked a place
        self.occupied: dict[str, int] = {}

        for drone, route in routes.items():
            if len(route) < 2:
                continue

            self.step[drone] = 0
            self.occupied[route[0]] = self.occupied.get(route[0], 0) + 1

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

    def zone_capacity(self, name: str) -> int:
        """Return how many drones a zone can hold.

        Args:
            name (str): the zone name.

        Returns:
            int: the capacity, the whole fleet for the two hubs.
        """
        zone = self.by_name.get(name)

        if zone is None:
            return 1

        if str(zone["zone_name"]) in self.HUBS:
            return self.nb_drones

        metadata = zone.get("metadata", {})

        return self.read_number(metadata.get("max_drones", 1))

    def link_capacity(self, origin: str, target: str) -> int:
        """Return how many drones may fly one connection at once.

        Args:
            origin (str): the zone the connection leaves from.
            target (str): the zone it leads to.

        Returns:
            int: the capacity of the connection.
        """
        zone = self.by_name.get(origin)

        if zone is None:
            return 1

        for neighbor in zone.get("neighbors", []):
            if len(neighbor) < 2 or str(neighbor[0]) != target:
                continue

            return self.read_number(neighbor[1])

        return 1

    def link_key(self, origin: str, target: str) -> tuple[str, str]:
        """Return the key counting the use of one connection.

        A connection is bidirectional, so two drones crossing it in
        opposite directions share the same capacity.

        Args:
            origin (str): one end of the connection.
            target (str): the other end.

        Returns:
            tuple[str, str]: the key of that connection.
        """
        if origin <= target:
            return (origin, target)

        return (target, origin)

    def is_restricted(self, name: str) -> bool:
        """Tell whether reaching a zone costs two turns.

        Args:
            name (str): the zone name.

        Returns:
            bool: True when the zone is restricted.
        """
        zone = self.by_name.get(name)

        if zone is None:
            return False

        metadata = zone.get("metadata", {})

        return str(metadata.get("zone", "normal")) == self.RESTRICTED

    def connection_name(self, origin: str, target: str) -> str:
        """Return the name of the connection between two zones.

        Args:
            origin (str): the zone the drone leaves.
            target (str): the zone it heads to.

        Returns:
            str: the connection written as "zone1-zone2".
        """
        return f"{origin}-{target}"

    def remaining(self, drone: str) -> int:
        """Return how many steps a drone still has to fly.

        Args:
            drone (str): the drone identifier.

        Returns:
            int: the number of steps left on its route.
        """
        return len(self.routes[drone]) - 1 - self.step[drone]

    def arrived(self, drone: str) -> bool:
        """Tell whether a drone stands on the last step of its route.

        Args:
            drone (str): the drone identifier.

        Returns:
            bool: True when the drone reached the end zone.
        """
        return self.remaining(drone) == 0

    def deliver(self, drone: str) -> None:
        """Take a delivered drone out of the flight.

        Args:
            drone (str): the drone identifier.
        """
        del self.step[drone]
        self.delivered.add(drone)

    def land_flying(self) -> list[Move]:
        """Land every drone that spent the previous turn in the air.

        The subject forbids waiting on a connection, so the place was
        already booked when the flight started and the landing can
        never fail.

        Returns:
            list[Move]: the landings of this turn.
        """
        moves: list[Move] = []
        flights = sorted(self.flying, key=self.remaining)

        for drone in flights:
            origin = self.flying[drone][0]
            del self.flying[drone]

            name = self.routes[drone][self.step[drone]]
            arrived = self.arrived(drone)

            moves.append(Move.arrival(drone, origin, name, arrived))

            if arrived:
                self.deliver(drone)

        return moves

    def advance(self, landed: set[str]) -> list[Move]:
        """Try to move every drone one step further.

        Drones are handled from the one closest to the goal, so a
        drone that leaves a zone frees the place for the one behind it
        during the very same turn.

        Args:
            landed (set[str]): the drones that just came down from a
                connection this very turn. Reaching a restricted zone
                costs two turns, so their move is already done and
                they must not fly again before the next turn.

        Returns:
            list[Move]: the moves and the waits of this turn.
        """
        moves: list[Move] = []
        used: dict[tuple[str, str], int] = {}
        order = sorted(self.step, key=self.remaining)

        for drone in order:
            if drone in landed or drone in self.flying:
                continue

            route = self.routes[drone]
            index = self.step[drone]
            here = route[index]
            target = route[index + 1]
            key = self.link_key(here, target)

            room = self.occupied.get(target, 0) < self.zone_capacity(target)
            free = used.get(key, 0) < self.link_capacity(here, target)

            if not room or not free:
                moves.append(Move.wait(drone, here))
                continue

            used[key] = used.get(key, 0) + 1
            self.occupied[here] = self.occupied.get(here, 0) - 1
            self.occupied[target] = self.occupied.get(target, 0) + 1
            self.step[drone] = index + 1

            if self.is_restricted(target):
                # the place on the restricted zone is booked now, so
                # the drone is sure to land on the next turn
                self.flying[drone] = (
                    here,
                    self.connection_name(here, target),
                )
                moves.append(Move.flight(
                    drone, here, self.connection_name(here, target)
                ))
                continue

            arrived = self.arrived(drone)

            moves.append(Move.arrival(drone, here, target, arrived))

            if arrived:
                self.deliver(drone)

        return moves

    def occupancy(self) -> dict[str, list[str]]:
        """Return which drones stand on which zone.

        A drone in the air is counted on the zone it booked, which is
        the zone it is bound to land on during the next turn.

        Returns:
            dict[str, list[str]]: zone name -> drone identifiers.
        """
        standing: dict[str, list[str]] = {}

        for drone, index in self.step.items():
            standing.setdefault(self.routes[drone][index], []).append(drone)

        for drone in self.delivered:
            end = self.routes[drone][-1]
            standing.setdefault(end, []).append(drone)

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
        return len(self.delivered) >= len(self.routes)

    def longest_route(self) -> int:
        """Return the number of steps of the longest route.

        Returns:
            int: the length of the longest route, zero when the fleet
            has nowhere to go.
        """
        lengths = [len(route) - 1 for route in self.routes.values()]

        if not lengths:
            return 0

        return max(lengths)

    def run(self, max_turns: int = 0) -> list[TurnRecord]:
        """Play the whole flight.

        Args:
            max_turns (int): safety limit, computed from the fleet and
                the routes when it is left to zero.

        Returns:
            list[TurnRecord]: one (moves, occupancy) pair
            per turn.
        """
        longest = self.longest_route()

        if longest < 1 or not self.step:
            return []

        if max_turns <= 0:
            max_turns = (self.nb_drones + 2) * (longest + 2)

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
