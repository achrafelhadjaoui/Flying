"""Schema of the first line of a map file."""

from typing import Literal

from pydantic import BaseModel, PositiveInt


class FirstLineValidator(BaseModel):
    """The 'nb_drones: <positive_integer>' declaration."""

    nb_drones_key: Literal["nb_drones"]
    nb_drones: PositiveInt
