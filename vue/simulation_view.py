from typing import Any

from .abstract_view import BaseView
from .terminal import Terminal
from .turn_view import Move, TurnView

ZoneData = dict[str, Any]


class SimulationView(BaseView):
    """Collect the turns and describe the whole flight.

    The subject asks for two things at once: a line per turn in a
    strict format, and a coloured feedback of the drone movements and
    of the zone states. Both are produced from the same turns, so they
    can never disagree.
    """

    def __init__(self, zones: list[ZoneData], nb_drones: int,
                 terminal: Terminal | None = None,
                 verbose: bool = True, max_lines: int = 12) -> None:
        """Prepare the report.

        Args:
            zones (list): every zone of the network.
            nb_drones (int): how many drones have to be delivered.
            terminal (Terminal | None): the colour helper.
            verbose (bool): True to describe each turn, False to print
                only the lines required by the subject.
            max_lines (int): how many movements are detailed per turn.
        """
        self.zones = zones
        self.nb_drones = nb_drones
        self.terminal = terminal if terminal is not None else Terminal()
        self.verbose = verbose
        self.max_lines = max_lines
        self.turns: list[TurnView] = []

    def add_turn(self, moves: list[Move],
                 occupancy: dict[str, list[str]] | None = None) -> TurnView:
        """Record one more turn.

        Args:
            moves (list): the Move objects played during the turn.
            occupancy (dict | None): zone name -> drones standing
                there once the turn is over.

        Returns:
            TurnView: the view built for that turn.
        """
        turn = TurnView(
            len(self.turns) + 1,
            moves,
            self.zones,
            occupancy,
            self.terminal,
            self.max_lines,
        )
        self.turns.append(turn)

        return turn

    def official_output(self) -> str:
        """Build only the lines required by the subject.

        Returns:
            str: one line per turn, in the expected format.
        """
        return "\n".join(turn.official_line() for turn in self.turns)

    def delivery_turns(self) -> dict[str, int]:
        """Find the turn on which each drone was delivered.

        Returns:
            dict[str, int]: drone identifier -> turn number.
        """
        delivered: dict[str, int] = {}

        for turn in self.turns:
            for move in turn.moves:
                if move.delivered and move.drone not in delivered:
                    delivered[move.drone] = turn.number

        return delivered

    def total_path_cost(self) -> int:
        """Return the cost in turns spent by all the drones together.

        A normal move counts for one turn, and a restricted one counts
        for two because it is made of a flight then a landing.

        Returns:
            int: the sum of the movement costs.
        """
        cost = 0

        for turn in self.turns:
            for move in turn.moves:
                if move.kind != Move.WAIT:
                    cost += 1

        return cost

    def metrics(self) -> dict[str, float]:
        """Compute the figures used to compare two solutions.

        Returns:
            dict[str, float]: the turn count, the average number of
            drones moved per turn, the average number of turns needed
            per drone and the total path cost.
        """
        delivered = self.delivery_turns()
        moved = 0

        for turn in self.turns:
            moved += turn.counters()[0]

        turns = len(self.turns)
        average_moved = moved / turns if turns else 0.0

        if delivered:
            average_turns = sum(delivered.values()) / len(delivered)
        else:
            average_turns = 0.0

        return {
            "turns": float(turns),
            "delivered": float(len(delivered)),
            "moves_per_turn": average_moved,
            "turns_per_drone": average_turns,
            "path_cost": float(self.total_path_cost()),
        }

    def render_header(self) -> str:
        """Build the few lines opening the report.

        Returns:
            str: the heading of the simulation.
        """
        title = self.terminal.paint("  Simulation", "", True)
        detail = self.terminal.paint(
            f"{self.nb_drones} drone(s) over {len(self.zones)} zones",
            "grey",
        )

        return f"{title}   {detail}\n"

    def render_metrics(self) -> str:
        """Build the closing report with the final figures.

        Returns:
            str: the summary of the simulation.
        """
        figures = self.metrics()
        turns = int(figures["turns"])
        delivered = int(figures["delivered"])

        lines: list[str] = ["", self.terminal.paint("  Result", "", True)]

        if delivered < self.nb_drones:
            lines.append(self.terminal.paint(
                f"    only {delivered}/{self.nb_drones} drone(s) reached "
                f"the end zone",
                "red",
                True,
            ))
        else:
            lines.append(self.terminal.paint(
                f"    all {delivered} drone(s) delivered", "green", True
            ))

        lines.append(
            "    total turns          "
            + self.terminal.paint(str(turns), "cyan", True)
        )
        lines.append(
            "    drones moved / turn  "
            f"{figures['moves_per_turn']:.2f}"
        )
        lines.append(
            "    turns / drone        "
            f"{figures['turns_per_drone']:.2f}"
        )
        lines.append(
            "    total path cost      "
            f"{int(figures['path_cost'])}"
        )

        return "\n".join(lines)

    def render(self) -> str:
        """Build the whole report.

        Returns:
            str: the turns and the final figures when the view is
            verbose, otherwise only the required output lines.
        """
        if not self.verbose:
            return self.official_output()

        blocks: list[str] = [self.render_header()]

        for turn in self.turns:
            blocks.append(turn.render())
            blocks.append("")

        blocks.append(self.render_metrics())

        return "\n".join(blocks)
