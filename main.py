import sys
from controller import validate_data
from controller.logic_handling import ShortPath
from parsing import Parser
from controller import ZoneController



def main() -> None:
    """the starting of the project where we read from terminal commands
    """
    
    if (len(sys.argv) != 2) :
        print("enter path of file")
        exit(3)
    file = ""
    try:
        file = Parser()
        file.file_check(sys.argv[1])
        file.first_line_check()
        file.zone_check()
        file.connection_check()
        validate_data(file.data)
        
        number_of_zones = len(file.data["zones"])
        for i in range(number_of_zones):
            zone_data = file.data["zones"][i]
            zone_controller = ZoneController(
                zone_data["zone_name"],
                zone_data["name"],
                zone_data["x_coordinate"],
                zone_data["y_coordinate"],
                zone_data["metadata"].get("color", ""),
                zone_data["metadata"].get("max_drones", 1),
                zone_data["metadata"].get("zone", "normal")
            )
            zone_controller.connect_connection(file.data) 
            
        # finding the shortest path between the start and the end zone
        start_zone = None
        end_zone = None
        for zone in file.data["zones"]:
            if zone["zone_name"] == "start_hub":
                start_zone = zone
            elif zone["zone_name"] == "end_hub":
                end_zone = zone

        if start_zone is None or end_zone is None:
            raise ValueError("the map needs a start_hub and an end_hub")

        short_path = ShortPath(start_zone, end_zone, file.data["zones"])
        short_path.find_shortest_path()

        if not short_path.path:
            print("no route found between the start and the end zone")
        else:
            route = " -> ".join(zone["name"] for zone in short_path.path)
            print(f"shortest path: {route}")
            print(f"cost: {short_path.total_cost} turns")
        
        
        #print(f"zones: {file.data['zones']}")
        # creatiing instances from the zone_controller to connect the zones with the connections
        
        #print(file.data["zones"][1])
        #print(file.data)
    except Exception as e:
        print(str(e))
        exit(3)
    #print(file.content)
    
    
        
        
        
        
    
main()