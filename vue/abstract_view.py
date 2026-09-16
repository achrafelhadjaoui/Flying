from abc import ABC, abstractmethod


class BaseView(ABC):
    """A piece of the terminal interface.

    A view never prints by itself: it builds a string and lets the
    caller decide what to do with it, which keeps the rendering easy
    to test and to redirect to a log file.
    """

    @abstractmethod
    def render(self) -> str:
        """Build the text of the view.

        Returns:
            str: the block of text to display.
        """
        pass

    def show(self) -> None:
        """Print the rendered view on the standard output."""
        print(self.render())
