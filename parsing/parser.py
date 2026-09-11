from errors import (
    FileNotReadable,
    FileNotFound,
    EmptyFileError,
    OsFileError,
    InvalidFirstLineError,
    InvalidFormatError,
    InvalidValueError,
)

class Parser():
    """a calss that responsible for passing all the data within the files
    """
    def __init__(self):
        """initialisation of the parser
        """
        self.content = ""
        self.first_line = ""
    
    def file_check(self, file_path) -> None:
        """ afunction that responsible for checking the availability of the file
        """
        try:
            with open(file_path, "r") as file:
                if not file.read(1):
                    raise EmptyFileError(f"File '{file_path}' is empty")
                    

            

        except FileNotFoundError:
            raise FileNotFound(f"File '{file_path}' was not found")

        except PermissionError:
            raise FileNotReadable(f"File '{file_path}' is not readable")
        except OSError:
            raise OsFileError("os file error")
            
        

        
            
        
# try:
#     obj = Parser()
#     obj.file_check("maps/easy/01_linear_path.txt")
#     obj.clean_content()
#     print(obj.content)

# except (Exception) as e:
#     print(e)