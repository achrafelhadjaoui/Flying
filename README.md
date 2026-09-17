*This project has been created as part of the 42 curriculum by aelhadja.*

# Fly-in

## Description

Fly-in is a Python project that simulates a fleet of drones travelling through a network of connected zones.

The program reads a map file, validates its content, builds the graph, looks for every route the capacities of the map allow between the start hub and the end hub using the A* algorithm, shares the fleet between those routes, and then simulates the movement of the drones while respecting the rules of the project.

The project is written in Python and uses Pydantic for data validation.

### Features

* Map file parsing with clear line-based error messages.
* Data validation using Pydantic.
* Graph construction from the map connections.
* A* pathfinding algorithm.
* Several routes per map, with the fleet distributed across them.
* Support for different zone types and capacities.
* Drone movement simulation, every drone carrying its own route.
* Turn by turn output in the format required by the subject,
  every zone written in the colour the map file gives it.

## Instructions

### Requirements

* Python 3.11 or later
* [uv](https://docs.astral.sh/uv/)

### Installation

Install the project dependencies with:

```bash
make install
```

This runs:

```bash
uv sync
```

### Running

Run the program with a map file:

```bash
uv run main.py maps/easy/01_linear_path.txt
```

You can also use the Makefile:

```bash
make run MAP=maps/easy/01_linear_path.txt
```

To run another map:

```bash
make run MAP=maps/hard/01_maze_nightmare.txt
```

### Debugging

Run the program with the Python debugger:

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

### Code checking

Run Flake8 and Mypy:

```bash
make lint
```

Run the stricter Mypy configuration:

```bash
make lint-strict
```

Clean generated Python files and caches:

```bash
make clean
```

## Project Layout

```text
.
├── controller/          # Graph, A*, flight plan and simulation
├── data_validation/     # Pydantic validation
├── errors/              # Custom exceptions
├── model/               # Zone and data models
├── parsing/             # Map file parsing
├── vue/                 # Terminal views
├── maps/                # Map files
├── main.py              # Program entry point
├── Makefile
└── pyproject.toml
```

## Algorithm Choices and Implementation Strategy

### Parsing

The parser reads the map file and processes its content line by line.

It removes comments and empty lines, then validates the different sections of the map.

Invalid syntax, duplicated zones, invalid connections, missing hubs and other input errors are reported with the corresponding line number.

Nothing may be declared twice: a zone name and a pair of coordinates belong to one single zone, a connection is declared once whatever the order of its two zones, and a metadata block carries at most one `color`, one `max_drones`, one `zone` and one `max_link_capacity`.

### Data Validation

Pydantic models are used after parsing to validate the values contained in the map.

For example, zone types, coordinates and capacities are checked before the simulation starts.

### Graph Construction

The connections from the map are converted into a graph.

Each zone stores information about its neighbours and their connection capacities. This allows the pathfinding and simulation code to access the graph directly without repeatedly parsing the original connections.

### A* Pathfinding

The project uses the A* algorithm to find a route from the start hub to the end hub.

A* uses two costs:

* `g(n)` — the real cost required to reach the current zone.
* `h(n)` — an estimated cost from the current zone to the end hub.

The algorithm combines them:

```text
f(n) = g(n) + h(n)
```

The heuristic uses the coordinates of the zones to estimate the remaining distance.

Zone types also affect the path cost:

* `normal`: normal movement cost.
* `priority`: normal movement cost with priority used when costs are equal.
* `restricted`: higher movement cost.
* `blocked`: cannot be entered.

### Multiple Paths and Fleet Distribution

One single route lets one drone through per turn at best, so sending
the whole fleet on the cheapest route makes the drones queue on the
start hub. The subject asks instead for the drones to be distributed
across several paths, which `FlightPlan` does in three steps.

**1. Collecting candidate routes.**

* The first candidates are the routes that can all be flown at the
  same time. Every route found books one place on each zone it crosses
  and one place on each connection it uses, then A* is run again on
  what is left, until nothing can be shared any more. A zone holding
  three drones therefore carries three routes, a connection of
  capacity one is used by a single route, and a route wide enough for
  two drones simply comes out twice.
* The other candidates are the detours: for each connection of a route
  already found, A* is run again with that single connection
  forbidden. This is what gives the fleet several tails over a shared
  corridor, for instance when three slow restricted branches leave the
  same narrow hub. Such routes cannot be flown fully in parallel, but
  they pay off as soon as the branches are slower than the corridor
  feeding them.

**2. Sharing the drones out.**

Each drone is given the route on which it lands the earliest, which is
the cost of the route plus the queue already sent on it. A route
crossing a restricted zone only accepts a new drone every other turn,
since a drone keeps its place booked while it flies over the
connection, so its queue counts double.

**3. Keeping only what helps.**

A candidate route is kept only when the whole flight really gets
shorter with it, which is measured by playing the simulation. The plan
starts from the cheapest route alone, so it can never end up worse
than a single route, and a route set the simulation cannot fly, for
instance two routes crossing the same connection in opposite
directions, is simply dropped.

### Drone Simulation

Once the plan is built, the simulation moves the drones turn by turn.

Every drone carries its own route, so the zones and the connections
are counted by name rather than by step, since two routes often share
a piece of the network. Drones closest to their goal are moved first,
which frees a place for the drone behind during the very same turn.

The scheduler checks the project rules before allowing a drone to move, including:

* Zone capacity.
* Connection capacity.
* Restricted-zone movement.
* Drone positions.
* Waiting when movement is not possible.

The simulation continues until all drones reach the end hub or the simulation detects that no further movement is possible.

## Simulation Output

The program prints the output required by section VII.5 of the subject
and nothing else.

Each turn is one line, listing the movements of that turn space
separated. A movement is written `D<ID>-<zone>`, or `D<ID>-<connection>`
while a drone is still flying towards a restricted zone, the connection
keeping the name it is declared with in the map file. A drone that does
not move is left out of its line, and a drone that reaches the end zone
is delivered and never printed again.

Every zone name is written in the colour its `color` metadata asks for,
a connection keeping the colour of each of the two zones it links. The
colours are ANSI escapes, dropped on their own as soon as the output is
not a terminal, so a redirected run stays exactly the plain text the
subject asks for.

## Example

### Input

Example map:

```text
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

Run it with:

```bash
uv run main.py maps/easy/02_simple_fork.txt
```

### Expected output

```text
  Simulation output

D1-junction D2-junction
D1-path_a D2-path_b D3-junction D4-junction
D1-goal D2-goal D3-path_a D4-path_b
D3-goal D4-goal
```

The two branches of the fork are used at the same time, so the four
drones are delivered in four turns instead of the six the single
cheapest route would need.

The exact number of turns and movements depends on the map and its capacity constraints.

## Performance

Turns needed on the maps provided with the subject, against the
targets of section VII.7:

| Map | Drones | Target | Turns |
| --- | --- | --- | --- |
| easy/01_linear_path | 2 | 6 | 4 |
| easy/02_simple_fork | 4 | 8 | 4 |
| easy/03_basic_capacity | 4 | 6 | 4 |
| medium/01_dead_end_trap | 5 | 12 | 8 |
| medium/02_circular_loop | 6 | 15 | 15 |
| medium/03_priority_puzzle | 5 | 12 | 7 |
| hard/01_maze_nightmare | 8 | 30 | 13 |
| hard/02_capacity_hell | 12 | 35 | 16 |
| hard/03_ultimate_challenge | 15 | 45 | 26 |
| challenger/01_the_impossible_dream | 25 | 45 (record) | 43 |

On every one of those maps the turn count matches the limit imposed by
the narrowest cut of the map, which is the cost of the cheapest route
plus the time the fleet needs to cross that cut.

## Resources

### A* and Pathfinding

* Amit Patel — Introduction to A*
  https://www.redblobgames.com/pathfinding/a-star/introduction.html

* Amit Patel — Heuristics for Grid Maps
  https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html

* Hart, Nilsson & Raphael — A Formal Basis for the Heuristic Determination of Minimum Cost Paths, 1968.

* Edsger W. Dijkstra — A Note on Two Problems in Connexion with Graphs, 1959.

### Python

* Python documentation — `abc` and `typing`
  https://docs.python.org/3/library/abc.html

* Pydantic documentation
  https://docs.pydantic.dev/

* Mypy documentation
  https://mypy.readthedocs.io/

* PEP 257 — Docstring Conventions
  https://peps.python.org/pep-0257/

### AI Usage

AI was used as a development and reviewing assistant.

It was used for:

* Understanding and reviewing the A* algorithm.
* Reviewing the parser and validation logic.
* Identifying potential bugs and edge cases.
* Helping with Python type hints and Mypy errors.
* Helping configure the Makefile and development tools.
* Reviewing and improving the README documentation.

The project architecture, algorithms and implementation were developed and understood by the author. No external graph library was used for the A* implementation.
