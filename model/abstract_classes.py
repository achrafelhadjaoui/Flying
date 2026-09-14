from abc import ABC, abstractmethod

class Zone(ABC):
    """a class represent zone model
    """

    def __init__(self, zone_name:str, name:str, x_coordinate:int, y_coordinate:int, color:str = "", capacity:int = 1, zone_type:str = "normal"):
        """init function to initilise given needed data
        """
        self.zone_name = zone_name
        self.name = name
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.color = color
        self.capacity = capacity
        self.zone_type = zone_type
        self.connections = []

    @abstractmethod
    def my_conections(self, data:dict) -> list[list]:
        """an abstract function that must extract every connection with the zone
        """
        pass

    


