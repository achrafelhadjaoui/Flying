from typing import Any

from .logic_handling import ShortPath
from .simulation import Simulation

ZoneData = dict[str, Any]


class FlightPlan:
    """Choose the routes of the fleet and share the drones out.

    One single route lets one drone through per turn at best, so
    sending the whole fleet on the cheapest one makes the drones queue
    on the start hub. The subject (VII.1) asks instead for the drones
    to be distributed across several paths, and for the routing to
    adapt itself to the map it is given.

    The plan is therefore built in three steps:

    * a pool of candidate routes is collected. The first ones are the
      routes that can be flown all at the same time, every route found
      booking one place on each zone it crosses and one place on each
      connection it uses until nothing is left to share. The others
      are the detours going round one connection of those routes,
      which is what gives the fleet several tails over a shared
      corridor, for instance when three slow restricted branches leave
      the same narrow hub,
    * the drones are shared out between the chosen routes, each of
      them taking the route on which it lands the earliest,
    * a route is only kept when the flight really gets shorter with
      it, which is measured by playing the whole simulation. The plan
      starts from the cheapest route alone, so it can never end up
      worse than a single route.
    """

    HUBS: tuple[str, ...] = ("start_hub", "end_hub")

    RESTRICTED: str = "restricted"

    # how many routes are tried before the plan settles, which keeps
    # the number of simulations played under control on a wide map
    MAX_CANDIDATES: int = 24

    # the score of a route set that cannot deliver the fleet
    IMPOSSIBLE: int = 1 << 30

    def __init__(self, start: ZoneData, end: ZoneData,
                 zones: list[ZoneData], nb_drones: int) -> None:
        """Prepare the plan of the whole flight.

        Args:
            start (ZoneData): the start hub.
            end (ZoneData): the end hub.
            zones (list[ZoneData]): every zone of the network.
            nb_drones (int): how many drones have to be delivered.
        """
        self.start = start
        self.end = end
        self.zones = zones
        self.nb_drones = nb_drones
        self.by_name: dict[str, ZoneData] = {
            str(zone["name"]): zone for zone in zones
        }

        # the routes kept, and one load per route
        self.paths: list[list[str]] = []
        self.loads: list[int] = []

        # drone -> the zone names it has to fly over
        self.routes: dict[str, list[str]] = {}

        # how many turns the plan needs, as played by the simulation
        self.turns: int = 0

    def read_number(self, value: Any, fallback: int = 1) -> int:
        """Read a capacity written either as a text or as a number.

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

    def zone_room(self, name: str) -> int:
        """Return how many drones a zone holds at the same time.

        Args:
            name (str): the zone name.

        Returns:
            int: its capacity, the whole fleet for the two hubs whose
            max_drones is ignored by the subject.
        """
        zone = self.by_name.get(name)

        if zone is None:
            return 1

        if str(zone["zone_name"]) in self.HUBS:
            return self.nb_drones

        metadata = zone.get("metadata", {})

        return self.read_number(metadata.get("max_drones", 1))

    def link_room(self, origin: str, target: str) -> int:
        """Return how many drones one connection carries at once.

        Args:
            origin (str): the zone the connection leaves from.
            target (str): the zone it leads to.

        Returns:
            int: the capacity of that connection.
        """
        zone = self.by_name.get(origin)

        if zone is None:
            return 1

        for neighbor in zone.get("neighbors", []):
            if len(neighbor) < 2 or str(neighbor[0]) != target:
                continue

            return self.read_number(neighbor[1])

        return 1

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

    def path_cost(self, path: list[str]) -> int:
        """Return how many turns one lonely drone spends on a route.

        Args:
            path (list[str]): the zone names of the route.

        Returns:
            int: the sum of the movement costs of the route.
        """
        cost = 0

        for name in path[1:]:
            cost += 2 if self.is_restricted(name) else 1

        return cost

    def path_period(self, path: list[str]) -> int:
        """Return how often a route accepts a new drone.

        A drone crossing a restricted zone spends one turn on the
        connection and one more to land, and it keeps its place booked
        the whole time, so the drone behind it only starts every other
        turn.

        Args:
            path (list[str]): the zone names of the route.

        Returns:
            int: the number of turns between two drones.
        """
        for name in path[1:-1]:
            if self.is_restricted(name):
                return 2

        return 1

    def search(self, banned: set[str],
               banned_links: set[tuple[str, str]]) -> list[str]:
        """Look for the cheapest route left by the given bans.

        Args:
            banned (set[str]): the zones the route may not cross.
            banned_links (set[tuple[str, str]]): the connections the
                route may not use.

        Returns:
            list[str]: the zone names of the route, empty when there
            is none.
        """
        search = ShortPath(
            self.start,
            self.end,
            self.zones,
            banned,
            banned_links,
        )
        search.find_shortest_path()

        return [str(zone["name"]) for zone in search.path]

    def take_room(self, path: list[str], room: dict[str, int],
                  links: dict[tuple[str, str], int], banned: set[str],
                  banned_links: set[tuple[str, str]]) -> None:
        """Book the places one route needs along its way.

        A zone or a connection left without any place is banned, so
        the next search has to look somewhere else.

        Args:
            path (list[str]): the zone names of the route.
            room (dict[str, int]): places left on every zone.
            links (dict[tuple[str, str], int]): places left on every
                connection.
            banned (set[str]): the zones that are full.
            banned_links (set[tuple[str, str]]): the connections that
                are full.
        """
        # the two hubs hold the whole fleet, only what is in between
        # can run out of room
        for name in path[1:-1]:
            room[name] = room.get(name, self.zone_room(name)) - 1

            if room[name] < 1:
                banned.add(name)

        for index in range(len(path) - 1):
            origin = path[index]
            target = path[index + 1]
            key = ShortPath.link_key(origin, target)

            links[key] = links.get(key, self.link_room(origin, target)) - 1

            if links[key] < 1:
                banned_links.add(key)

    def lane_paths(self) -> list[list[str]]:
        """Collect the routes that can all be flown at the same time.

        The same route comes out twice when its zones and its
        connections are wide enough to carry two drones side by side.

        Returns:
            list[list[str]]: the routes, cheapest first.
        """
        paths: list[list[str]] = []

        room: dict[str, int] = {}
        links: dict[tuple[str, str], int] = {}
        banned: set[str] = set()
        banned_links: set[tuple[str, str]] = set()

        # more routes than drones would never be used
        while len(paths) < self.nb_drones:
            path = self.search(banned, banned_links)

            if not path:
                break

            paths.append(path)
            self.take_room(path, room, links, banned, banned_links)

        return paths

    def detour_paths(self, paths: list[list[str]]) -> list[list[str]]:
        """Collect the routes going round one connection of another.

        Two routes sharing a corridor are useless when the corridor is
        what slows the fleet down, but they pay off as soon as they
        split into branches that are slower than the corridor itself.

        Args:
            paths (list[list[str]]): the routes to walk round.

        Returns:
            list[list[str]]: the detours found, without any repetition.
        """
        found: list[list[str]] = []

        for path in paths:
            for index in range(len(path) - 1):
                banned_links = {
                    ShortPath.link_key(path[index], path[index + 1])
                }
                detour = self.search(set(), banned_links)

                if detour and detour not in paths and detour not in found:
                    found.append(detour)

        return found

    def candidates(self) -> list[list[str]]:
        """Build the pool of routes the plan chooses from.

        Returns:
            list[list[str]]: the candidate routes, cheapest first.
        """
        lanes = self.lane_paths()
        pool = lanes + self.detour_paths(lanes)

        pool.sort(key=self.path_cost)

        return pool[:self.MAX_CANDIDATES]

    def landing_turn(self, index: int) -> int:
        """Estimate the turn the next drone of a route would land on.

        Args:
            index (int): the route to look at.

        Returns:
            int: the cost of the route plus the queue already waiting
            on it.
        """
        path = self.paths[index]

        return (
            self.path_cost(path)
            + self.loads[index] * self.path_period(path)
        )

    def spread_drones(self) -> None:
        """Give every drone the route delivering it the earliest."""
        self.routes = {}
        self.loads = [0] * len(self.paths)

        if not self.paths:
            return

        for number in range(1, self.nb_drones + 1):
            best = 0

            for index in range(1, len(self.paths)):
                if self.landing_turn(index) < self.landing_turn(best):
                    best = index

            self.routes[f"D{number}"] = list(self.paths[best])
            self.loads[best] += 1

    def play(self) -> int:
        """Play the current plan and return the turns it needs.

        The simulation is the only judge: it enforces every rule of
        the subject, so a route set it cannot fly is simply dropped.

        Returns:
            int: the number of turns, IMPOSSIBLE when the fleet does
            not make it to the end zone.
        """
        flight = Simulation(self.zones, self.routes, self.nb_drones)
        turns = flight.run()

        if flight.deadlock or not flight.finished():
            return self.IMPOSSIBLE

        return len(turns)

    def select(self, pool: list[list[str]]) -> None:
        """Keep the routes that really shorten the flight.

        Args:
            pool (list[list[str]]): the candidate routes, cheapest
                first.
        """
        self.paths = [pool[0]]
        self.spread_drones()
        best = self.play()

        for path in pool[1:]:
            kept = self.paths

            self.paths = kept + [path]
            self.spread_drones()
            turns = self.play()

            if turns < best:
                best = turns
                continue

            # that route brings nothing, the fleet stays as it was
            self.paths = kept
            self.spread_drones()

        self.turns = best

    def build(self) -> None:
        """Find the routes and share the fleet between them."""
        pool = self.candidates()

        if not pool:
            self.paths = []
            self.routes = {}
            self.loads = []
            return

        self.select(pool)
