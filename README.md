*This project has been created as part of the 42 curriculum by aelhadja.*

# Fly-in

## Description

Fly-in routes a fleet of autonomous drones through a network of connected
zones, from a single start hub to a single end hub, in as few simulation
turns as possible.

A map file describes the network: how many drones take off, the zones with
their coordinates and their metadata, and the connections between them.
The program reads that file, checks it line by line, builds the graph,
searches the cheapest route with an A* algorithm, then plays the flight
turn after turn while respecting every occupancy and movement rule of the
subject. Each turn is printed twice: once as the strict output line the
subject asks for, and once as a coloured, human readable description of
what every drone did.

The whole project is written in plain Python 3.11 with no graph library at
all: the graph, the priority queue and the scheduling are implemented by
hand.

### Features

- A parser that reports the **line and the cause** of every syntax error.
- A pydantic schema layer that checks the value of every field.
- An A* search weighted by the zone types (`restricted` costs two turns,
  `priority` is preferred at equal cost, `blocked` is never entered).
- A turn scheduler honouring `max_drones`, `max_link_capacity`, the
  two-turn flights towards restricted zones, and strategic waiting.
- A coloured terminal view with per-turn occupancy and final metrics.

## Instructions

### Requirements

- Python **3.11** or later
- [uv](https://docs.astral.sh/uv/) (or plain `pip`)

### Installation

```bash
make install          # uv sync: dependencies + dev tools (flake8, mypy)
```

With pip instead:

```bash
python3 -m venv .venv
.venv/bin/pip install pydantic flake8 mypy
```

### Running

The program takes exactly one argument: the path of a map file.

```bash
.venv/bin/python main.py maps/easy/01_linear_path.txt
```

Or through the Makefile, which defaults to the first easy map:

```bash
make run                                        # default map
make run MAP=maps/hard/01_maze_nightmare.txt    # any other map
make maps                                       # every map at once
make debug MAP=maps/medium/02_circular_loop.txt # under pdb
```

### Checking the code

```bash
make lint          # flake8 . and mypy . with the flags of the subject
make lint-strict   # flake8 . and mypy . --strict
make clean         # remove __pycache__ and .mypy_cache
```

Both targets pass with no error.

## Project layout

The code follows a model / view / controller split:

| Folder             | Role                                                      |
| ------------------ | --------------------------------------------------------- |
| `parsing/`         | reads the file and checks its syntax, line by line         |
| `data_validation/` | pydantic schemas checking the value of every field         |
| `errors/`          | the exception hierarchy, each one carrying a code and line |
| `model/`           | `AbstractZone` and the concrete `Zone`                     |
| `controller/`      | graph building, A* search and turn scheduling              |
| `vue/`             | the terminal views and the colour handling                 |
| `maps/`            | the maps provided with the subject                         |

## Algorithm choices and implementation strategy

### 1. Parsing

`Parser` walks the file once. Comments (`#`, whole line or trailing) and
empty lines are dropped by `clean_line`, then three passes read the
`nb_drones` declaration, the zones and the connections. The zone block
ends at the first `connection:` line, so the hubs may be declared in any
order inside that block.

The parser rejects, with the guilty line number: a missing or non positive
`nb_drones`, an unknown line prefix, a duplicated zone name, a zone name
containing a dash, a missing or duplicated hub, a malformed metadata
block, a connection pointing at an unknown zone, and the same connection
declared twice in either direction (`a-b` and `b-a`).

`data_validation` then checks the values with pydantic: the zone type must
be one of `normal`, `blocked`, `restricted` or `priority`, and the two
capacities must be positive integers. The colour is kept as a free string,
since the subject accepts any single word.

### 2. Building the graph

`ZoneController` inherits the `Zone` model and, for each zone, collects
every connection it appears in as `[neighbour name, link capacity]`.
Those neighbour lists are written back into the parsed data, so the search
and the simulation walk the graph without ever scanning the connections
again. Building the graph is `O(Z x C)` for `Z` zones and `C` connections,
done once at startup.

### 3. Pathfinding: A*

`ShortPath` is an A* search. Dijkstra alone would work, but the maps carry
coordinates, so the Manhattan distance to the goal is free information and
A* explores fewer zones for the same answer.

- **g(n)**, the real cost, is the sum of the zone costs on the way: one
  turn for `normal` and `priority`, two turns for `restricted`.
  `blocked` zones are dropped, never queued.
- **h(n)** is the Manhattan distance to the goal divided by the longest
  single connection of the map (`max_connection_span`), rounded up. That
  division is what keeps the heuristic **admissible**: without it the
  distance is counted in grid units while g(n) is counted in turns, the
  heuristic overestimates and the route found may not be the cheapest.
- Ties on f(n) are broken in favour of `priority` zones, which is how the
  subject's "should be prioritized in pathfinding" is honoured without
  ever preferring a genuinely more expensive route.
- A zone is **settled** the first time it leaves the queue, and
  `best_cost` keeps the cheapest g(n) seen per zone, so a zone is never
  expanded twice.
- The route is rebuilt from the `came_from` links once the goal is
  reached.

The priority queue is a sorted list, kept ordered on insertion, since no
library is allowed. Insertion is `O(n)`, so the search costs
`O(Z^2 + C)` in the worst case. With maps of a few dozen zones this is
instant, and the route is computed **once** and cached for the whole
flight, never recomputed per drone or per turn. Memory is `O(Z)`: one
entry per zone in `came_from`, `best_cost` and the queue.

### 4. Turn scheduling

`Simulation` replays the route turn after turn, and this is where the
occupancy rules live.

- `occupied[i]` counts the drones standing on step `i` of the route. A
  drone flying towards a restricted zone **already counts** on the step it
  will land on, which is how the subject's "it cannot wait on the
  connection" rule is guaranteed: the slot is booked when the flight
  starts, so the landing can never fail.
- Drones are handled **from the one closest to the goal backwards**, so a
  drone leaving a zone frees its place for the drone behind it during the
  very same turn, exactly as VII.3 requires.
- A move needs both room in the destination zone (`max_drones`, ignored on
  the two hubs) and a free slot on the connection (`max_link_capacity`),
  counted per turn in `used`.
- A drone that cannot move stays in place and is reported as waiting; it
  is omitted from the official output line.
- A drone that lands from a flight has already used its turn and is
  skipped by `advance`, so reaching a restricted zone really costs two
  turns.
- If a whole turn passes with nobody moving and nobody in flight, the run
  stops and reports a deadlock instead of looping forever.

One turn costs `O(D)` for `D` drones, so the whole flight is
`O(D x T)` for `T` turns, with `O(D)` memory.

### Known limitation

The scheduler currently sends the whole fleet down the **single** cheapest
route. Every rule of the subject is respected and every reference target
is met, but on a map offering several disjoint routes the drones queue up
instead of spreading out. Splitting the fleet over several routes is the
natural next step, and it is what would bring the challenger map back
under its record.

## Visual representation

The subject asks for visual feedback of the simulation; this project does
it with a coloured terminal view built on plain ANSI escape sequences, so
no colour library is needed.

- `Terminal` maps a colour name to an ANSI 256 tone. The subject allows
  **any** single word as a colour, so unknown names get a stable readable
  tone derived from a checksum of the name, never `hash()`, whose value
  changes between two runs. Colours are switched off automatically when
  the output is piped to a file, or when `NO_COLOR` / `TERM=dumb` is set,
  so a log file never contains escape sequences.
- `TurnView` describes a single turn: which drone moved from where to
  where, painted in the colour asked in the map, plus the type of the
  destination zone and how full it is (`2/3`, or `2/-` for the hubs which
  have no limit). Drones in flight towards a restricted zone are shown
  with a `...>` arrow and the reminder that they must land next turn,
  waiting drones are grouped on one line, and a long turn is truncated so
  a fleet of eighty drones stays readable.
- Every turn also prints the **exact output line** required by the
  subject, right under its own description, so the reader can check the
  strict format and the human explanation against each other.
- `SimulationView` closes with the metrics used to compare two solutions:
  total turns, drones moved per turn, turns per drone and total path cost.

A view never prints by itself: `BaseView.render()` returns a string and
the caller decides what to do with it, which keeps the output easy to test
or to redirect.

## Example

Input, `maps/easy/02_simple_fork.txt`:

```
# Easy Level 2: Simple fork with two paths
nb_drones: 4

start_hub: start 0 0 [color=green]
hub: junction 1 0 [color=yellow max_drones=2]
hub: path_a 2 1 [color=blue]
hub: path_b 2 -1 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-junction [max_link_capacity=2]
connection: junction-path_a
connection: junction-path_b
connection: path_a-goal
connection: path_b-goal
```

Output (colours removed):

```
shortest path: start -> junction -> path_a -> goal
cost: 3 turns

  Simulation   4 drone(s) over 5 zones

  Turn 1   2 moved, 2 waiting, 0 delivered
    D1               start ---> junction           normal        2/2
    D2               start ---> junction           normal        2/2
    waiting: D3 D4

    output: D1-junction D2-junction

  Turn 2   2 moved, 2 waiting, 0 delivered
    D1            junction ---> path_a             normal        1/1
    D3               start ---> junction           normal        2/2
    waiting: D2 D4

    output: D1-path_a D3-junction

  ...

  Result
    all 4 drone(s) delivered
    total turns          6
    drones moved / turn  2.00
    turns / drone        4.50
    total path cost      12
```

The `output:` lines, taken together, are the format required by VII.5:

```
D1-junction D2-junction
D1-path_a D3-junction
D1-goal D2-path_a D4-junction
D2-goal D3-path_a
D3-goal D4-path_a
D4-goal
```

A drone still flying towards a restricted zone appears as
`D1-<zone1>-<zone2>`, the name of the connection it occupies.

### Error handling

Every error stops the program with a clear message naming the line and the
cause:

```
$ .venv/bin/python main.py broken.txt
[INVALID_VALUE] Line 4: The zone name 'b' is already used on line 3
```

## Performance

Measured with `make maps`, against the reference targets of VII.7:

| Map                            | Drones | Target | Result  |
| ------------------------------ | -----: | -----: | ------: |
| easy / linear path             |      2 |    ≤ 6 |   **4** |
| easy / simple fork             |      4 |    ≤ 8 |   **6** |
| easy / basic capacity          |      4 |    ≤ 6 |   **4** |
| medium / dead end trap         |      5 |   ≤ 12 |   **8** |
| medium / circular loop         |      6 |   ≤ 15 |  **15** |
| medium / priority puzzle       |      5 |   ≤ 12 |   **8** |
| hard / maze nightmare          |      8 |   ≤ 30 |  **13** |
| hard / capacity hell           |     12 |   ≤ 35 |  **16** |
| hard / ultimate challenge      |     15 |   ≤ 45 |  **26** |
| challenger / impossible dream  |     25 |     45 |      67 |

Every mandatory target is met. The optional challenger map is solved, all
25 drones are delivered, but the single-route scheduling described above
keeps it above the reference record.

## Resources

Documentation and articles used:

- Amit Patel, *Introduction to A\**, Red Blob Games —
  <https://www.redblobgames.com/pathfinding/a-star/introduction.html>
- Amit Patel, *Heuristics for grid maps* —
  <https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html>
- Hart, Nilsson & Raphael, *A Formal Basis for the Heuristic Determination
  of Minimum Cost Paths*, IEEE, 1968 — the original A* paper
- Edsger W. Dijkstra, *A note on two problems in connexion with graphs*,
  1959
- Python documentation, `abc` and `typing` modules —
  <https://docs.python.org/3/library/abc.html>
- pydantic documentation —
  <https://docs.pydantic.dev/latest/>
- mypy documentation, command line flags —
  <https://mypy.readthedocs.io/en/stable/command_line.html>
- PEP 257, *Docstring Conventions* —
  <https://peps.python.org/pep-0257/>
- ANSI escape codes, for the coloured terminal output —
  <https://en.wikipedia.org/wiki/ANSI_escape_code>

### Use of AI

AI was used as a reviewing and tidying assistant, never as a substitute
for the design:

- **Reviewing**, on the parser and the simulation: reading the subject
  against the code and pointing at the rules that were not enforced. This
  is how four real defects were found and fixed — colours restricted to a
  fixed list while the subject allows any word, the zone type never
  validated, the zone block stopping at `end_hub` so the subject's own
  example could not be read, and a drone landing from a restricted flight
  being allowed to move again in the same turn, which made restricted
  zones cost one turn instead of two.
- **Tooling**, for the `Makefile` and the flake8 / mypy configuration.
- **Tidying**, to bring the whole code base to flake8 and `mypy --strict`
  with type hints and PEP 257 docstrings everywhere.
- **Writing**, for the first draft of this README.

The design decisions — the MVC split, the exception hierarchy, the A*
with its admissible heuristic and the priority tie-break, the booking of
the destination slot when a flight starts — were made and are fully
understood by the author, and the algorithms are hand written with no
graph library, as the subject demands.
