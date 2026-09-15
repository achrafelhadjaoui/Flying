# class ShortPath():
#     def __init__(self, start, end, data):
#         """function that initilise the zone start point and end point

#         Args:
#             start (int): start zone node
#             end (int): goal zone node
#         """
        
#         self.start = start
#         self.end = end
#         self.data = data
#         self.min_heap = [tuple]
#         self.is_found = set()
#         self.path = []
            
#     def count_estimated_number(self, prev_cost:int, node) -> tuple:
#         """a fuuction that count the estimated nuumber for heuristic algo

#         Args:
#             node (dict): the zone that will couunt it's estimated number
#             prev_cost (int): the previouse node's cost
            

#         Returns:
#             tuple: the estimated number and the flag
#         """
#         cost = 0
#         meta_data = node['meta_data']
#         zone_type = meta_data.get('zone', "normal")
#         if zone_type == "normal" or zone_type == "priority":
#             cost = 1
#         elif zone_type == "restricted":
#             cost = 2
            
            
#         gn = cost + prev_cost
            
#         goal_x = self.end['x_coordinate']
#         goal_y = self.end['y_coordinate']
        
#         current_x = node['x_coordinate']
#         current_y = node['y_coordinate']

        
        
        
            
#         hn = (goal_x - current_x) + (goal_y - current_y)
#         fn = gn + hn
#         return (fn, zone_type)
        
        
#     def apply_min_heap(self, cost:int, node:dict, flag:str):
#         """a function that is responsible for applying min heap algo over the stored processed nodes

#         Args:
#             cost (int): cost of the node
#             node (dict): node we want to be ordered as a min heap
#             flag (str): flags that responsible for addding node's cost.
#         """
        
#         if flag != "blocked":
#             if flag == "priority":
#                 i = 0
#                 while i < len(self.min_heap):
#                     prev_zone = self.min_heap[i]
#                     type_zone  = prev_zone[1]['metadata'].get('zone', "normal")
#                     if type_zone == flag:
#                         #choose the smallest cost
#                         prev_cost = prev_zone[0]
#                         if prev_cost <= cost:
#                             i +=1
#                             continue
#                     else:
#                         self.min_heap.insert(i, (cost, node))
#                         break
#             else:
#                 # add it to min_heap based on it's cost
#                 size = len(self.min_heap)
#                 i = 0
#                 while i < size:
#                     prev_zone = self.min_heap[i]
#                     prev_cost = prev_zone[0]
#                     if prev_cost <= cost:
#                         i += 1
#                         continue
#                     else:
#                         self.min_heap.insert(i, (cost, node))
#                         break
                        
#                 if i == size:
#                     self.min_heap.append((cost, node))
                        
                        
                    

#     def append_neighbors(self, neighbor_name:str, prev_cost):
#         """function to add neighbors to min_heap queue

#         Args:
#             neighbor_name (str): the previoouusly finding neighbor name
#             prev_cost (int): the previouse counted costs
            
#         """
        
#         for item in self.data:
#             if item['name'] == neighbor_name:
#                 if item in self.is_found:
#                     break
#                 else:
#                     cost, flag = self.count_estimated_number(prev_cost,item)
#                     self.apply_min_heap(cost, item, flag)
#                     self.is_found.add(item)
#                     break
#             else:
#                 continue
                            
                
                

#     def find_shortest_path(self) -> None:
#         """a function that responsible for finding the shortest paht from the current node into the goal

#         Args:
#             data (dict): dictionary that conatin the extracted data
#         """
        
#         self.min_heap.append((0, self.start))
#         self.is_found.add(self.start)
#         while (self.min_heap):
#             current_node = self.min_heap.pop(0)
#             self.path.append(current_node[1])
#             if current_node[1] == self.end:
#                 break
#             for item in current_node[1]['neighbors']:
#                 self.append_neighbors(item, current_node[0])
        
        
            
                
                
            
        
                
                
                
        

class ShortPath:
    def __init__(self, start, end, data):
        """Initialize the start and end zones.

        Args:
            start (dict): start zone node.
            end (dict): goal zone node.
            data (list): list of all zone nodes.
        """

        self.start = start
        self.end = end
        self.data = data
        self.min_heap = []
        self.is_found = set()
        self.path = []

    def count_estimated_number(self, prev_cost: int, node) -> tuple:
        """Calculate the estimated cost of a node.

        Args:
            prev_cost (int): cost of the previous node.
            node (dict): zone node to evaluate.

        Returns:
            tuple: estimated cost and zone type.
        """

        cost = 0
        meta_data = node["metadata"]
        zone_type = meta_data.get("zone", "normal")

        if zone_type == "normal" or zone_type == "priority":
            cost = 1
        elif zone_type == "restricted":
            cost = 2

        gn = cost + prev_cost

        goal_x = self.end["x_coordinate"]
        goal_y = self.end["y_coordinate"]

        current_x = node["x_coordinate"]
        current_y = node["y_coordinate"]

        # Manhattan distance
        hn = abs(goal_x - current_x) + abs(goal_y - current_y)

        fn = gn + hn

        return (fn, zone_type)

    def apply_min_heap(self, cost: int, node: dict, flag: str):
        """Insert a node into the min heap according to its cost.

        Args:
            cost (int): calculated f(n) cost.
            node (dict): zone node.
            flag (str): zone type.
        """

        if flag == "blocked":
            return

        if not self.min_heap:
            self.min_heap.append((cost, node))
            return

        if flag == "priority":
            i = 0
            while i < len(self.min_heap):
                prev_zone = self.min_heap[i]
                prev_cost = prev_zone[0]
                prev_type = prev_zone[1]["metadata"].get(
                    "zone",
                    "normal"
                )

                if prev_type == "priority":
                    if prev_cost <= cost:
                        i += 1
                        continue

                    self.min_heap.insert(i, (cost, node))
                    return

                self.min_heap.insert(i, (cost, node))
                return

            self.min_heap.append((cost, node))
            return

        size = len(self.min_heap)
        i = 0

        while i < size:
            prev_zone = self.min_heap[i]
            prev_cost = prev_zone[0]

            if prev_cost <= cost:
                i += 1
                continue

            self.min_heap.insert(i, (cost, node))
            return

        self.min_heap.append((cost, node))

    def append_neighbors(self, neighbor_name: str, prev_cost: int):
        """Add a neighbor to the min heap.

        Args:
            neighbor_name (str): name of the neighbor zone.
            prev_cost (int): cost of the previous node.
        """
        for item in self.data:
            if item["name"] != neighbor_name:
                continue

            if item["name"] in self.is_found:
                break
               
            cost, flag = self.count_estimated_number(
                prev_cost,
                item
            )

            self.apply_min_heap(cost, item, flag)
            self.is_found.add(item["name"])
            break

    def find_shortest_path(self) -> None:
        """Find the shortest path from the start zone to the end zone."""

        self.min_heap.append((0, self.start))
        self.is_found.add(self.start["name"])

        while self.min_heap:
            current_node = self.min_heap.pop(0)
            current_zone = current_node[1]

            self.path.append(current_zone)

            if current_zone == self.end:
                break

            for neighbor in current_zone["neighbors"]:
                self.append_neighbors(
                    neighbor[0],
                    current_node[0]
                )
