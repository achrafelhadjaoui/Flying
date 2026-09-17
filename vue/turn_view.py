from typing import Any

from .abstract_view import BaseView
from .terminal import Terminal

ZoneData = dict[str, Any]


class Move:
    """One action taken by one drone during a turn.

    The subject knows three of them: reaching a zone, flying over a
    connection towards a restricted zone, and staying in place.
    """

    ARRIVAL: str = "arrival"
    FLIGHT: str = "flight"
    WAIT: str = "wait"

    def __init__(self, drone: str, origin: str, target: str,
                 kind: str, delivered: bool = False) -> None:
        """Store one action.

        Args:
            drone (str): the drone identifier, for instance "D1".
            origin (str): the zone the drone comes from.
            target (str): the zone reached, or the connection flown
                over when the drone is still in the air.
            kind (str): ARRIVAL, FLIGHT or WAIT.
            delivered (bool): True when the target is the end zone.
        """
        self.drone = drone
        self.origin = origin
        self.target = target
        self.kind = kind
        self.delivered = delivered

    @classmethod
    def arrival(cls, drone: str, origin: str, zone: str,
                delivered: bool = False) -> "Move":
        """Build the action of a drone reaching a zone.

        Args:
            drone (str): the drone identifier.
            origin (str): the zone left behind.
            zone (str): the zone reached.
            delivered (bool): True when that zone is the end zone.

        Returns:
            Move: the matching action.
        """
        return cls(drone, origin, zone, cls.ARRIVAL, delivered)

    @classmethod
    def flight(cls, drone: str, origin: str, connection: str) -> "Move":
        """Build the action of a drone still over a connection.

        A restricted zone costs two turns, so the drone spends the
        first one on the connection and MUST land on the next one.

        Args:
            drone (str): the drone identifier.
            origin (str): the zone left behind.
            connection (str): the connection name, "zone1-zone2".

        Returns:
            Move: the matching action.
        """
        return cls(drone, origin, connection, cls.FLIGHT)

    @classmethod
    def wait(cls, drone: str, zone: str) -> "Move":
        """Build the action of a drone staying where it is.

        Args:
            drone (str): the drone identifier.
            zone (str): the zone the drone stays in.

        Returns:
            Move: the matching action.
        """
        return cls(drone, zone, zone, cls.WAIT)


class TurnView(BaseView):
    """Tell what every drone did during a single turn.

    Two things are produced: the line required by the subject, and a
    coloured description of the same turn meant for a human reader.
    """

    def __init__(self, number: int, moves: list[Move],
                 zones: list[ZoneData] | None = None,
                 occupancy: dict[str, list[str]] | None = None,
                 terminal: Terminal | None = None,
                 max_lines: int = 12) -> None:
        """Prepare the description of one turn.

        Args:
            number (int): the turn number, starting at one.
            moves (list): the Move objects of that turn.
            zones (list | None): the zones, used for their colour,
                their type and their capacity.
            occupancy (dict | None): zone name -> drones standing
                there at the end of the turn.
            terminal (Terminal | None): the colour helper.
            max_lines (int): how many movements are detailed before
                the rest is only counted, which keeps a fleet of
                eighty drones readable.
        """
        self.number = number
        self.moves = moves
        self.max_lines = max_lines
        self.zones = zones if zones is not None else []
        self.occupancy = dict(occupancy) if occupancy else {}
        self.terminal = terminal if terminal is not None else Terminal()
        self.by_name: dict[str, ZoneData] = {
            str(zone["name"]): zone for zone in self.zones
        }

    def paint_zones(self, target: str) -> str:
        """Write a zone or a connection with the colour of its zones.

        A zone name never holds a dash, so a connection is simply the
        two zones it links written around one. Both of them therefore
        keep the colour asked for in the map file, and the dash
        between them stays plain.

        Args:
            target (str): the zone name, or the connection name.

        Returns:
            str: the name, every zone painted with its own colour.
        """
        return "-".join(
            self.terminal.paint(name, self.zone_color(name))
            for name in target.split("-")
        )

    def official_token(self, move: Move) -> str:
        """Build one coloured piece of the official turn line.

        Args:
            move (Move): the action to write.

        Returns:
            str: "D<ID>-<zone>" or "D<ID>-<connection>", the zones
            painted with their colour, empty when the drone waited.
        """
        if move.kind == Move.WAIT:
            return ""

        return f"{move.drone}-{self.paint_zones(move.target)}"

    def official_line(self) -> str:
        """Build the line required by the subject.

        Every movement of the turn is listed, space separated, and the
        drones that did not move are left out. Each zone is written in
        the colour the map file gave it, which the terminal drops on
        its own when the output is not a terminal.

        Returns:
            str: the turn line, empty when nothing moved.
        """
        tokens = [self.official_token(move) for move in self.moves]

        return " ".join(token for token in tokens if token)

    def zone_type(self, name: str) -> str:
        """Return the type of a zone.

        Args:
            name (str): the zone name.

        Returns:
            str: the zone type, "normal" by default.
        """
        zone = self.by_name.get(name)

        if zone is None:
            return "normal"

        return str(zone.get("metadata", {}).get("zone", "normal"))

    def zone_color(self, name: str) -> str:
        """Return the colour asked for a zone.

        Args:
            name (str): the zone name.

        Returns:
            str: the colour name, empty when none was given.
        """
        zone = self.by_name.get(name)

        if zone is None:
            return ""

        return str(zone.get("metadata", {}).get("color", ""))

    def capacity_of(self, name: str) -> str:
        """Return how full a zone is at the end of the turn.

        Args:
            name (str): the zone name.

        Returns:
            str: something like "2/3", or "2/-" when the zone has no
            limit, which is the case of the start and the end zones.
        """
        used = len(self.occupancy.get(name, []))
        zone = self.by_name.get(name)

        if zone is None:
            return f"{used}/?"

        if str(zone["zone_name"]) in ("start_hub", "end_hub"):
            return f"{used}/-"

        room = zone.get("metadata", {}).get("max_drones", 1)

        return f"{used}/{room}"

    def describe(self, move: Move) -> str:
        """Build the coloured line describing one action.

        Args:
            move (Move): the action to describe.

        Returns:
            str: one line of description.
        """
        drone = self.terminal.paint(f"{move.drone:<4}", "", True)

        if move.kind == Move.WAIT:
            zone = self.terminal.paint(
                f"{move.origin}", self.zone_color(move.origin)
            )
            return (
                f"    {drone} waits in {zone} "
                f"{self.terminal.paint('(blocked or holding back)', 'grey')}"
            )

        origin = self.terminal.paint(
            f"{move.origin:>18}", self.zone_color(move.origin)
        )

        if move.kind == Move.FLIGHT:
            arrow = self.terminal.paint(" ...> ", "grey")
            target = self.terminal.paint(f"{move.target:<18}", "orange")
            note = self.terminal.paint(
                "in flight, must land next turn", "grey"
            )
            return f"    {drone}{origin}{arrow}{target} {note}"

        arrow = self.terminal.paint(" ---> ", "grey")
        kind = self.zone_type(move.target)
        target = self.terminal.paint(
            f"{move.target:<18}", self.zone_color(move.target)
        )

        details = f"{kind:<11}{self.capacity_of(move.target):>6}"

        if move.delivered:
            details += self.terminal.paint("  delivered", "green", True)

        return f"    {drone}{origin}{arrow}{target} {details}"

    def counters(self) -> tuple[int, int, int]:
        """Count what happened during the turn.

        Returns:
            tuple[int, int, int]: how many drones moved, waited and
            were delivered.
        """
        moved = 0
        waiting = 0
        delivered = 0

        for move in self.moves:
            if move.kind == Move.WAIT:
                waiting += 1
            else:
                moved += 1
            if move.delivered:
                delivered += 1

        return (moved, waiting, delivered)

    def render(self) -> str:
        """Build the whole description of the turn.

        Returns:
            str: the heading and one line per drone. The line required
            by the subject is not repeated here, the whole simulation
            prints it in one single block.
        """
        moved, waiting, delivered = self.counters()

        heading = self.terminal.paint(f"  Turn {self.number}", "", True)
        summary = self.terminal.paint(
            f"{moved} moved, {waiting} waiting, {delivered} delivered",
            "grey",
        )

        lines: list[str] = [f"{heading}   {summary}"]

        # the real movements first, they are what the reader looks for
        active = [one for one in self.moves if one.kind != Move.WAIT]
        idle = [one for one in self.moves if one.kind == Move.WAIT]

        for move in active[:self.max_lines]:
            lines.append(self.describe(move))

        hidden = len(active) - self.max_lines

        if hidden > 0:
            lines.append(self.terminal.paint(
                f"    ... and {hidden} more movement(s)", "grey"
            ))

        if idle:
            names = " ".join(one.drone for one in idle[:self.max_lines])

            if len(idle) > self.max_lines:
                names += f" ... (+{len(idle) - self.max_lines})"

            lines.append(
                "    " + self.terminal.paint("waiting: ", "grey") + names
            )

        return "\n".join(lines)
