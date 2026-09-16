*This project has been created as part of the 42 curriculum by aelhadja.*

# Fly-in

## Description

Fly-in is a Python project that simulates a fleet of drones travelling through a network of connected zones.

The program reads a map file, validates its content, builds the graph, finds a route from the start hub to the end hub using the A* algorithm, and then simulates the movement of the drones while respecting the rules of the project.

The project is written in Python and uses Pydantic for data validation.

### Features

* Map file parsing with clear line-based error messages.
* Data validation using Pydantic.
* Graph construction from the map connections.
* A* pathfinding algorithm.
* Support for different zone types and capacities.
* Drone movement simulation.
* Coloured terminal output showing the simulation.

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
├── controller/          # Graph, A* and simulation logic
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

The path is calculated once and then used by the simulation.

### Drone Simulation

After the route is found, the simulation moves the drones turn by turn.

The scheduler checks the project rules before allowing a drone to move, including:

* Zone capacity.
* Connection capacity.
* Restricted-zone movement.
* Drone positions.
* Waiting when movement is not possible.

The simulation continues until all drones reach the end hub or the simulation detects that no further movement is possible.

## Visual Representation

The program provides a coloured terminal representation of the simulation.

The output shows:

* The current turn.
* Drone movements.
* Drone positions.
* Zone occupancy.
* Waiting drones.
* Simulation results.

Colours make different zones and drone movements easier to distinguish while keeping the simulation output readable.

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
shortest path: start -> junction -> path_a -> goal
cost: 3 turns

Turn 1
D1-junction D2-junction

Turn 2
D1-path_a D3-junction

...

Result
all drones delivered
```

The exact number of turns and movements depends on the map and its capacity constraints.

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
