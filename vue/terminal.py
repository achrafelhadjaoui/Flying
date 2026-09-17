import os
import sys


class Terminal:
    """Turn colour names into ANSI sequences.

    The subject says a colour may be any single word and that there is
    no fixed list, so known names are mapped to a close ANSI tone and
    unknown ones get a stable tone derived from the name itself.
    """

    RESET: str = "\033[0m"

    # names met in the maps, plus the usual extras
    KNOWN: dict[str, int] = {
        "black": 240,
        "grey": 245,
        "gray": 245,
        "white": 255,
        "silver": 250,
        "red": 196,
        "darkred": 88,
        "crimson": 161,
        "maroon": 52,
        "brown": 130,
        "orange": 208,
        "gold": 220,
        "yellow": 226,
        "olive": 100,
        "lime": 118,
        "green": 46,
        "teal": 30,
        "cyan": 51,
        "blue": 33,
        "navy": 26,
        "purple": 129,
        "violet": 177,
        "magenta": 201,
        "pink": 218,
        "rainbow": 213,
    }

    # readable tones used when a colour name is unknown
    FALLBACK: tuple[int, ...] = (
        39, 43, 78, 113, 148, 178, 209, 175, 141, 105,
    )

    def __init__(self, enabled: bool | None = None) -> None:
        """Prepare the colour output.

        Args:
            enabled (bool | None): force colours on or off. When left
                to None the terminal is inspected instead.
        """
        if enabled is None:
            enabled = self.detect_support()

        self.enabled: bool = enabled

    def detect_support(self) -> bool:
        """Tell whether colours can be written on the output.

        Colours are dropped when the output is redirected to a file or
        when the usual NO_COLOR / TERM=dumb conventions ask for it.

        Returns:
            bool: True when escape sequences may be used.
        """
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("TERM", "") == "dumb":
            return False
        return sys.stdout.isatty()

    def code_of(self, color: str) -> int:
        """Return the ANSI 256 code matching a colour name.

        Args:
            color (str): the colour written in the map file.

        Returns:
            int: an ANSI 256 colour code.
        """
        name = color.strip().lower()

        if name in self.KNOWN:
            return self.KNOWN[name]

        # a stable checksum, never hash(), whose value changes between
        # two runs unless PYTHONHASHSEED is fixed
        total = 0
        for position, letter in enumerate(name, start=1):
            total += ord(letter) * position

        return self.FALLBACK[total % len(self.FALLBACK)]

    def paint(self, text: str, color: str = "", bold: bool = False,
              reverse: bool = False) -> str:
        """Wrap a piece of text in the requested ANSI sequences.

        Args:
            text (str): the text to decorate.
            color (str): the colour name, empty for the default one.
            bold (bool): whether the text is written in bold.
            reverse (bool): whether the colours are swapped, which is
                used to point at a zone without changing its colour.

        Returns:
            str: the decorated text, unchanged when colours are off.
        """
        if not self.enabled:
            return text

        codes: list[str] = []

        if bold:
            codes.append("1")
        if reverse:
            codes.append("7")
        if color:
            codes.append(f"38;5;{self.code_of(color)}")

        if not codes:
            return text

        return f"\033[{';'.join(codes)}m{text}{self.RESET}"
