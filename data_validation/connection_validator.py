from pydantic import BaseModel, ValidationError

class ConnectionValidator(BaseModel):
    start_zone: str 
    end_zone: str
    distance: int