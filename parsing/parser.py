from typing import Any

from errors import (
    FileNotReadable,
    FileNotFound,
    EmptyFileError,
    OsFileError,
    InvalidFirstLineError,
    InvalidFormatError,
    InvalidValueError,
)


class Parser:
    """A class responsible for parsing all the data within the files."""

    # the three prefixes that open a zone declaration
    ZONE_KEYS: tuple[str, ...] = ("start_hub", "end_hub", "hub")

    # the tags a zone line may carry between its brackets
    ZONE_METADATA_KEYS: tuple[str, ...] = ("color", "max_drones", "zone")

    # the only tag a connection line may carry
    LINK_METADATA_KEYS: tuple[str, ...] = ("max_link_capacity",)

    def __init__(self) -> None:
        """Initialisation of the parser."""
        self.content: list[str] = []
        self.first_line: str = ""
        self.data: dict[str, Any] = {}
        self.file_index: int = 0

    def clean_line(self, line: str) -> str:
        """Drop the comment part of a line and the useless spaces.

        Args:
            line (str): one raw line of the file.

        Returns:
            str: the line without its comment, empty when there is
            nothing left to read on it.
        """
        if "#" in line:
            line = line.split("#", 1)[0]

        return line.strip()

    def file_check(self, file_path: str) -> None:
        """Check the availability and the content of the file.

        Args:
            file_path (str): path of the map file to read.
        """
        try:
            with open(file_path, "r") as file:
                content = file.read()

            if not content.strip():
                raise EmptyFileError(file_path)

            self.content = content.splitlines()

        except FileNotFoundError:
            raise FileNotFound(file_path)

        except PermissionError:
            raise FileNotReadable(file_path)
        except OSError:
            raise OsFileError(file_path)

    def first_line_check(self) -> None:
        """Check the first readable line of the file."""
        if not self.content:
            raise InvalidFirstLineError(self.file_index)

        index = 0

        for index, line in enumerate(self.content, start=1):
            line = self.clean_line(line)

            # skip the comments and the empty lines
            if not line:
                continue

            self.first_line = line
            break

        # point to the line right after the first readable one
        self.file_index = index

        if not self.first_line:
            raise InvalidFirstLineError(index)
        elif not self.first_line.startswith("nb_drones"):
            raise InvalidFirstLineError(index)
        elif self.first_line.count(":") != 1:
            raise InvalidFormatError(
                "The first line must contain exactly one ':'",
                index,
            )
        elif not self.first_line.split(":")[1].strip().isdigit():
            raise InvalidValueError(
                "The value after 'nb_drones:' must be a valid integer",
                index,
            )

        key, value = self.first_line.split(":", 1)

        if int(value.strip()) < 1:
            raise InvalidValueError(
                "The number of drones must be a positive integer",
                index,
            )

        self.data[key.strip()] = int(value.strip())

    def zone_helper(self, zone: str, index: int) -> None:
        """Check the shape of a zone line.

        Args:
            zone (str): content of the current line within the file.
            index (int): number of that line within the file.
        """
        if zone.count(":") != 1:
            raise InvalidFormatError(
                "The line must contain exactly one ':'",
                index,
            )

    def check_zone_name(self, name: str, index: int) -> None:
        """Check that a zone name may be used in a connection.

        Args:
            name (str): the name read on the zone line.
            index (int): number of that line within the file.
        """
        if not name:
            raise InvalidValueError("The zone name cannot be empty", index)

        # a dash would make 'connection: a-b' impossible to split
        if "-" in name:
            raise InvalidValueError(
                f"The zone name '{name}' cannot contain a dash",
                index,
            )

        for zone in self.data["zones"]:
            if zone["name"] == name:
                raise InvalidValueError(
                    f"The zone name '{name}' is already used on line "
                    f"{zone['line']}",
                    index,
                )

    def check_coordinates(self, x: int, y: int, index: int) -> None:
        """Check that no zone sits on those coordinates already.

        Args:
            x (int): the x coordinate read on the zone line.
            y (int): the y coordinate read on the zone line.
            index (int): number of that line within the file.
        """
        for zone in self.data["zones"]:
            if (zone["x_coordinate"], zone["y_coordinate"]) == (x, y):
                raise InvalidValueError(
                    f"The coordinates ({x}, {y}) are already used by the "
                    f"zone '{zone['name']}' on line {zone['line']}",
                    index,
                )

    def check_metadata_keys(
        self,
        keys: list[str],
        allowed: tuple[str, ...],
        index: int,
    ) -> None:
        """Check the tags of one metadata block, twice is never allowed.

        Args:
            keys (list[str]): the keys read inside the brackets.
            allowed (tuple[str, ...]): the keys that block accepts.
            index (int): number of that line within the file.
        """
        seen: set[str] = set()

        for key in keys:
            if key not in allowed:
                raise InvalidValueError(
                    f"'{key}' is not a known metadata key, expected one "
                    f"of {', '.join(allowed)}",
                    index,
                )

            if key in seen:
                raise InvalidValueError(
                    f"The metadata key '{key}' is written twice on the "
                    f"same line, only one value is allowed",
                    index,
                )

            seen.add(key)

    def read_metadata(self, metadata: str, index: int) -> dict[str, str]:
        """Read the optional metadata block of a zone line.

        Args:
            metadata (str): the block, brackets included.
            index (int): number of that line within the file.

        Returns:
            dict[str, str]: the tags read inside the brackets.
        """
        data_attributes: dict[str, str] = {}

        if not metadata.startswith("[") or not metadata.endswith("]"):
            raise InvalidFormatError(
                "Metadata must be enclosed in square brackets",
                index,
            )

        metadata = metadata[1:-1]  # Remove the square brackets

        if not metadata.strip():
            raise InvalidValueError("Metadata cannot be empty", index)

        items = metadata.split()

        if not all("=" in item for item in items):
            raise InvalidFormatError(
                "Metadata items must be in the format key=value",
                index,
            )

        pairs = [item.split("=", 1) for item in items]

        if not all(key and value for key, value in pairs):
            raise InvalidValueError(
                "Metadata keys and values cannot be empty",
                index,
            )

        self.check_metadata_keys(
            [key for key, _ in pairs],
            self.ZONE_METADATA_KEYS,
            index,
        )

        if len(items) > 3:
            raise InvalidFormatError(
                "Metadata must contain between 1 and 3 items",
                index,
            )

        for key, value in pairs:
            data_attributes[key] = value

        return data_attributes

    def split_zone_line(self, line: str, index: int) -> None:
        """Split one zone line and store what it declares.

        Args:
            line (str): content of the current line within the file.
            index (int): number of that line within the file.
        """
        key, value = line.split(":", 1)

        key = key.strip()

        # name, x, y and the optional metadata block
        parts = value.strip().split(None, 3)

        if not key:
            raise InvalidValueError("The key cannot be empty", index)

        if len(parts) < 3:
            raise InvalidFormatError(
                "A zone must contain a name and two coordinates",
                index,
            )

        name = parts[0]

        self.check_zone_name(name, index)

        try:
            x_coordinate = int(parts[1])
            y_coordinate = int(parts[2])
        except ValueError as e:
            raise InvalidValueError(
                "Coordinates must be integers",
                index,
            ) from e

        self.check_coordinates(x_coordinate, y_coordinate, index)

        # the metadata block is optional, every tag then keeps its
        # default value
        data_attributes: dict[str, str] = {}

        if len(parts) == 4:
            data_attributes = self.read_metadata(parts[3], index)

        self.data["zones"].append({
            "line": index,
            "zone_name": key,
            "name": name,
            "x_coordinate": x_coordinate,
            "y_coordinate": y_coordinate,
            "metadata": data_attributes,
        })

    def check_hubs(self) -> None:
        """Check that the map holds one start hub and one end hub."""
        for wanted in ("start_hub", "end_hub"):
            found = [
                zone for zone in self.data["zones"]
                if zone["zone_name"] == wanted
            ]

            if not found:
                raise InvalidValueError(
                    f"The map must declare one '{wanted}' zone",
                    self.file_index,
                )

            if len(found) > 1:
                raise InvalidValueError(
                    f"The map declares {len(found)} '{wanted}' zones, "
                    f"only one is allowed",
                    found[1]["line"],
                )

    def zone_check(self) -> None:
        """Read every zone declared in the file."""
        self.data["zones"] = []
        index = self.file_index

        for index, line in enumerate(
            self.content[self.file_index:],
            start=self.file_index + 1,
        ):
            line = self.clean_line(line)

            if not line:
                continue

            # the connections open the second block of the file
            if line.startswith("connection"):
                break

            self.zone_helper(line, index)

            if line.split(":", 1)[0].strip() not in self.ZONE_KEYS:
                raise InvalidValueError(
                    "A zone line must start with 'start_hub:', "
                    "'end_hub:' or 'hub:'",
                    index,
                )

            self.split_zone_line(line, index)
        else:
            # no connection line at all, nothing is left to read
            index += 1

        # step back on the connection line so it is read again
        self.file_index = index - 1
        self.check_hubs()

    def known_zone(self, name: str, index: int) -> None:
        """Check that a connection points at an existing zone.

        Args:
            name (str): the zone name written in the connection.
            index (int): number of that line within the file.
        """
        for zone in self.data["zones"]:
            if zone["name"] == name:
                return

        raise InvalidValueError(
            f"The connection uses the unknown zone '{name}'",
            index,
        )

    def check_duplicate(self, zones: list[str], index: int) -> None:
        """Check that a connection is not declared twice.

        'a-b' and 'b-a' describe the same connection, and a zone is
        never linked to itself.

        Args:
            zones (list[str]): the two zones of the connection.
            index (int): number of that line within the file.
        """
        if zones[0] == zones[1]:
            raise InvalidValueError(
                f"The connection cannot link the zone '{zones[0]}' "
                f"to itself",
                index,
            )

        for connection in self.data["connections"]:
            if sorted(connection["description"]) == sorted(zones):
                raise InvalidValueError(
                    f"The connection '{zones[0]}-{zones[1]}' is already "
                    f"declared on line {connection['line']}",
                    index,
                )

    def read_link_metadata(self, block: str, index: int) -> tuple[str, str]:
        """Read the optional metadata block of a connection line.

        Args:
            block (str): the block, brackets included.
            index (int): number of that line within the file.

        Returns:
            tuple[str, str]: the tag name and its value.
        """
        if not block.startswith("[") or not block.endswith("]"):
            raise InvalidFormatError(
                "The metadata must be enclosed in square brackets",
                index,
            )

        metadata = block[1:-1]  # Remove the square brackets

        if not metadata.strip():
            raise InvalidValueError("The metadata cannot be empty", index)

        items = metadata.split()

        if not all("=" in item for item in items):
            raise InvalidFormatError(
                "The metadata must be in the format key=value",
                index,
            )

        self.check_metadata_keys(
            [item.split("=", 1)[0] for item in items],
            self.LINK_METADATA_KEYS,
            index,
        )

        if len(items) != 1:
            raise InvalidFormatError(
                "The metadata must contain exactly one capacity",
                index,
            )
        if metadata.count("=") != 1:
            raise InvalidFormatError(
                "The metadata must be in the format key=value",
                index,
            )
        if not metadata.split("=")[1].isdigit():
            raise InvalidValueError("The capacity must be an integer", index)

        key, value = metadata.split("=")

        return (key, value)

    def connection_check(self) -> None:
        """Read every connection declared in the file."""
        self.data["connections"] = []

        for index, line in enumerate(
            self.content[self.file_index:],
            start=self.file_index + 1,
        ):
            line = self.clean_line(line)

            if not line:
                continue
            if line.count(":") != 1:
                raise InvalidFormatError(
                    "The line must contain exactly one ':'",
                    index,
                )

            # the two zones and the optional metadata block
            parts = line.split(None, 2)

            if len(parts) > 3 or len(parts) < 2:
                raise InvalidFormatError(
                    "The line must contain exactly two or three items",
                    index,
                )
            if parts[0].strip() != "connection:":
                raise InvalidValueError(
                    "The line must start with 'connection'",
                    index,
                )

            if len(parts) == 3:
                metadata_key, metadata_value = self.read_link_metadata(
                    parts[2],
                    index,
                )
            else:
                metadata_key, metadata_value = "max_link_capacity", "1"

            connection_name = line.split(":", 1)[0].strip()
            description = parts[1].strip()

            if not description:
                raise InvalidValueError(
                    "The description cannot be empty",
                    index,
                )
            if description.count("-") != 1:
                raise InvalidFormatError(
                    "The description must contain exactly two zones "
                    "separated by a hyphen",
                    index,
                )
            if not all(zone.strip() for zone in description.split("-")):
                raise InvalidValueError(
                    "The zones in the description cannot be empty",
                    index,
                )

            zones = [part.strip() for part in description.split("-")]

            for zone_name in zones:
                self.known_zone(zone_name, index)

            self.check_duplicate(zones, index)

            self.data["connections"].append({
                "line": index,
                "connection_name": connection_name,
                "description": zones,
                "metadata": {metadata_key: metadata_value},
            })
