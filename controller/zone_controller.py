from model import Zone

class ZoneController(Zone):
    """Zone creation that is responsible for creating zone and it's connections
    """
    
    def __init__(self, zone_name:str, name:str, x_coordinate:int, y_coordinate:int, color:str = "", max_drones:int = 1, zone:str = "normal"):
        """init function to initilise given needed data
        """
        super().__init__(zone_name, name, x_coordinate, y_coordinate, color, max_drones, zone)
        
    # assign connection to the zone
    def connect_connection(self, data:dict) -> None:

        """a function that responsible for connecting the zone with the connection"""
        
        neighbors_data = []
        link_capacity: int = 1
        

        for connection in data["connections"]:
            data_list = []
            if self.name not in connection["description"]:
                continue

            if self.name in connection["description"]:
                for zone in connection["description"]:
                    if zone != self.name:
                        data_list.append(zone)
                link_capacity = connection["metadata"].get("max_link_capacity", 1)
                data_list.append(link_capacity)
                
            neighbors_data.append(data_list)
            
        data["zones"][Zone.index]["neighbors"] = neighbors_data
        Zone.index += 1