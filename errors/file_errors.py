class FileError(Exception):
    """Base exception for file-related errors."""

    code = "FILE_ERROR"

    def __init__(self, message: str,
                 file_path: str | None = None) -> None:
        self.message = message
        self.file_path = file_path
        super().__init__(message)

    def __str__(self) -> str:
        if self.file_path:
            return f"[{self.code}] {self.message}: '{self.file_path}'"
        return f"[{self.code}] {self.message}"


class FileNotFound(FileError):
    """Raised when the requested file does not exist."""

    code = "FILE_NOT_FOUND"

    def __init__(self, file_path: str) -> None:
        super().__init__("File was not found", file_path)


class FileNotReadable(FileError):
    """Raised when the file cannot be read."""

    code = "FILE_NOT_READABLE"

    def __init__(self, file_path: str) -> None:
        super().__init__("File is not readable", file_path)


class EmptyFileError(FileError):
    """Raised when the file contains no usable content."""

    code = "EMPTY_FILE"

    def __init__(self, file_path: str | None = None) -> None:
        super().__init__("File is empty", file_path)


class OsFileError(FileError):
    """Raised when an unexpected OS-level file error occurs."""

    code = "OS_FILE_ERROR"

    def __init__(self, file_path: str,
                 message: str = "OS error while accessing file") -> None:
        super().__init__(message, file_path)
