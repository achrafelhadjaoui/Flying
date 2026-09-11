from pydantic import BaseModel, ValidationError

class ZoneValidator(BaseModel):
    nb_drones_key : str | nb_drones