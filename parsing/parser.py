from errors import (
    FileNotReadable,
    FileNotFound,
    EmptyFileError,
    OsFileError,
    InvalidFirstLineError,
    InvalidFormatError,
    InvalidValueError,
)
from errors.parser_errors import MissingValueError

class Parser():
    """a calss that responsible for passing all the data within the files
    """
    def __init__(self):
        """initialisation of the parser
        """
        self.content = ""
        self.first_line = ""
        self.data = {}
        self.file_index = 0
    
    def file_check(self, file_path) -> None:
        """ afunction that responsible for checking the availability of the file
        """
        try:
            with open(file_path, "r") as file:
                self.content = file.read()
            
            if not self.content.strip():
                raise EmptyFileError(file_path)
            
            
        except FileNotFoundError:
            raise FileNotFound(file_path)

        except PermissionError:
            raise FileNotReadable(file_path)
        except OSError:
            raise OsFileError(file_path)
        
    def first_line_check(self) -> None:
        """a function that responsible for checking the first line of the file
        """
        
        self.content = self.content.splitlines()
        if not self.content:
            raise InvalidFirstLineError(self.file_index)
        
        for index, line in enumerate(self.content, start=1):
            if line.startswith("#"):
                continue  # Skip comment lines
            elif "#" in line:
                line = line.split("#", 1)[0].strip()  # Remove inline comments
            # check for empty line or containing only whitespace
            elif not line:
                continue  # Skip empty lines
            
            self.first_line = line
            break  # Stop after finding the first non-comment, non-empty line
        
        # increment the file_index to point to the next line after the first line
        self.file_index = index
        
        if not self.first_line:
            raise InvalidFirstLineError(index)
        elif not self.first_line.startswith("nb_drones"):
            raise InvalidFirstLineError(index)
        elif self.first_line.count(":") != 1:
            raise InvalidFormatError("The first line must contain exactly one ':'", index)
        elif not self.first_line.split(":")[1].strip().isdigit():
            raise InvalidValueError("The value after 'nb_drones:' must be a valid integer", index)
        
        key, value = self.first_line.split(":", 1)
        self.data[key.strip()] = int(value.strip())
        
    
    def zone_helper(self, zone:str, index:int) -> None:
        """a function helper that split every line zone

        Args:
            zone (str): zone contain the content of the current line within the file
            index (int): responsiible for t
        """
        if zone.count(":") != 1:
            raise InvalidFormatError("The line must contain exactly one ':'", index)
        

    def split_zone_line(self, line: str, index: int) -> None:
        """a function that responsible for splitting the line of the zone

        Args:
            line (str): contain the content of the current line within the file
            index (int): responsible for the line number within the file
        """
        data_attributes = {}
        key, value = line.split(":", 1)

        key = key.strip()
        
        parts = value.strip().split(None, 3)  # Split into at most 4 parts: name, x, y, metadata

        if not key:
            raise InvalidValueError("The key cannot be empty", index)

        if len(parts) < 4:
            raise InvalidFormatError(
                "A zone must contain a name and two coordinates and metadata",
                index
            )

        name = parts[0]

        try:
            x_coordinate = int(parts[1])
            y_coordinate = int(parts[2])
        except ValueError as e:
            raise InvalidValueError(
                "Coordinates must be integers",
                index
            ) from e
            
        self.data["zones"].append({
            "line": index,
            "zone_name": key,
            "name": name,
            "x_coordinate": x_coordinate,
            "y_coordinate": y_coordinate,
            "metadata": data_attributes,
            })
        
        metadata = parts[3]
        if not metadata.startswith("[") or not metadata.endswith("]"):
            raise InvalidFormatError(
                "Metadata must be enclosed in square brackets",
                index
            )
        metadata = metadata[1:-1]  # Remove the square brackets
        if not metadata:
            raise InvalidValueError(
                "Metadata cannot be empty",
                index
            )
        elif len(metadata.split()) < 1 or len(metadata.split()) > 3:
            raise InvalidFormatError(
                "Metadata must contain between 1 and 3 items",
                index
            )
        elif not all("=" in item for item in metadata.split()):
            raise InvalidFormatError(
                "Metadata items must be in the format key=value",
                index
            )
        metadata = metadata.split()
        for item in metadata:
            key, value = item.split("=", 1)
            if not key or not value:
                raise InvalidValueError(
                    "Metadata keys and values cannot be empty",
                    index
                )
            data_attributes[key] = value
            
        
    def zone_check(self) -> None:
        """a function that responsible for checking the zone of the file
        """
        self.data["zones"] = []
        
        for index, line in enumerate(self.content[self.file_index:], start=self.file_index+1):
            if line.startswith("#"):
                continue
            elif "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                self.zone_helper(line, index)
                self.split_zone_line(line, index)
                if line.startswith("end_hub"):
                    self.file_index = index # Update file_index to the line after the last zone
                    break
            except InvalidFormatError as e:
                raise e
            
    def connection_check(self) -> None:
        """a function that responsible for checking the connection of the file
        """
        self.data["connections"] = []
        
        for index, line in enumerate(self.content[self.file_index:], start=self.file_index+1):
            if line.startswith("#"):
                continue
            elif "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if line.count(":") != 1:
                raise InvalidFormatError("The line must contain exactly one ':'", index)
            if len(line.strip().split()) > 3 or len(line.strip().split()) < 2:
                raise InvalidFormatError("The line must contain exactly two or three items", index)
            if line.split()[0].strip() != "connection:":
                raise InvalidValueError("The line must start with 'connection'", index)
            if len(line.split()) == 3:
                if not line.split()[2].startswith("[") or not line.split()[2].endswith("]"):
                    raise InvalidFormatError("The metadata must be enclosed in square brackets", index)
                metadata = line.split()[2][1:-1]  # Remove the square brackets
                if not metadata:
                    raise InvalidValueError("The metadata cannot be empty", index)
                if len(metadata.split()) != 1:
                    raise InvalidFormatError("The metadata must contain exactly capacity", index)
                if metadata.count("=") != 1:
                    raise InvalidFormatError("The metadata must be in the format key=value", index)
                if not metadata.split("=")[1].isdigit():
                    raise InvalidValueError("The capacity must be an integer", index)
                metadata_key, metadata_value = metadata.split("=")
            connection_name = line.split(":", 1)[0].strip()
            description = line.split()[1].strip()
            self.data["connections"].append({
                "line": index,
                "connection_name": connection_name,
                "description": description,
                "metadata": {metadata_key: metadata_value}
            })
            
            
            
        
            
        
# try:
#     obj = Parser()
#     obj.file_check("maps/easy/01_linear_path.txt")
#     obj.clean_content()
#     print(obj.content)

# except (Exception) as e:
#     print(e)