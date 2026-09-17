class ParserError(Exception):
    """Base exception for parsing errors."""

    code = "PARSER_ERROR"

    def __init__(
        self,
        message: str,
        line: int | None = None,
    ) -> None:
        self.message = message
        self.line = line
        super().__init__(message)

    def __str__(self) -> str:
        if self.line is not None:
            return f"[{self.code}] Line {self.line}: {self.message}"
        return f"[{self.code}] {self.message}"


class InvalidFirstLineError(ParserError):
    """Raised when the first line is not the nb_drones declaration."""

    code = "INVALID_FIRST_LINE"

    def __init__(self, line: int = 1) -> None:
        super().__init__(
            "The first line must contain 'nb_drones'",
            line,
        )


class InvalidFormatError(ParserError):
    """Raised when a line does not follow the expected format."""

    code = "INVALID_FORMAT"

    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message, line)


class InvalidValueError(ParserError):
    """Raised when a parsed value has an invalid type or value."""

    code = "INVALID_VALUE"

    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message, line)
