class Zone():
    """a class represent zone model
    """
    # class index for tracking the cuurrent zone in the data
    index: int = 0
    
    def __init__(self, zone_name:str, name:str, x_coordinate:int, y_coordinate:int, color:str = "", max_drones:int = 1, zone:str = "normal"):
        """init function to initilise given needed data
        """
        self.zone_name = zone_name
        self.name = name
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.color = color
        self.capacity = max_drones
        self.zone_type = zone