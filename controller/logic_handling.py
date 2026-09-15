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
    def __init__(self, start: dict, end: dict, data: list) -> None:
        """Initialize the start and end zones.

        Args:
            start (dict): start zone node.
            end (dict): goal zone node.
            data (list): list of all zone nodes.
        """

        self.start = start
        self.end = end
        self.data = data
        self.min_heap: list[tuple] = []
        self.is_found: set[str] = set()
        self.path: list[dict] = []
        # zone name -> name of the zone we came from, used to rebuild
        # the route once the goal is reached
        self.came_from: dict[str, str] = {}
        # zone name -> best real cost g(n) known so far
        self.best_cost: dict[str, int] = {}
        self.total_cost: int = 0
        self.span = self.max_connection_span()

    def max_connection_span(self) -> int:
        """Return the longest Manhattan step of a single connection.

        One move can never bring a drone closer to the goal than this
        distance, so dividing the remaining distance by it keeps the
        heuristic below the real cost, which is what A* needs to stay
        optimal.

        Returns:
            int: the longest step, never below one.
        """

        span = 1

        for zone in self.data:
            for neighbor in zone.get("neighbors", []):
                if not neighbor:
                    continue

                for other in self.data:
                    if other["name"] != neighbor[0]:
                        continue

                    dx = abs(other["x_coordinate"] - zone["x_coordinate"])
                    dy = abs(other["y_coordinate"] - zone["y_coordinate"])

                    if dx + dy > span:
                        span = dx + dy
                    break

        return span

    def count_estimated_number(self, prev_cost: int,
                               node: dict) -> tuple:
        """Calculate the estimated cost of a node.

        Args:
            prev_cost (int): real cost g(n) of the previous node.
            node (dict): zone node to evaluate.

        Returns:
            tuple: estimated cost f(n), real cost g(n) and zone type.
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

        # Manhattan distance turned into a number of moves, otherwise
        # it counts grid units and largely overestimates g(n)
        distance = abs(goal_x - current_x) + abs(goal_y - current_y)
        hn = -(-distance // self.span)

        fn = gn + hn

        return (fn, gn, zone_type)

    def apply_min_heap(self, cost: int, real_cost: int, node: dict,
                       flag: str) -> None:
        """Insert a node into the min heap according to its cost.

        Args:
            cost (int): calculated f(n) cost.
            real_cost (int): real cost g(n) carried to the neighbors.
            node (dict): zone node.
            flag (str): zone type.
        """

        if flag == "blocked":
            return

        entry = (cost, node, real_cost)

        if not self.min_heap:
            self.min_heap.append(entry)
            return

        size = len(self.min_heap)
        i = 0

        while i < size:
            prev_zone = self.min_heap[i]
            prev_cost = prev_zone[0]

            if prev_cost < cost:
                i += 1
                continue

            if prev_cost == cost:
                prev_type = prev_zone[1]["metadata"].get(
                    "zone",
                    "normal"
                )

                # equal cost: a priority zone is explored first, but it
                # never jumps ahead of a genuinely cheaper zone
                if flag != "priority" or prev_type == "priority":
                    i += 1
                    continue

            self.min_heap.insert(i, entry)
            return

        self.min_heap.append(entry)

    def append_neighbors(self, neighbor_name: str, prev_cost: int,
                         prev_name: str) -> None:
        """Add a neighbor to the min heap.

        Args:
            neighbor_name (str): name of the neighbor zone.
            prev_cost (int): real cost g(n) of the previous node.
            prev_name (str): name of the previous zone.
        """
        for item in self.data:
            if item["name"] != neighbor_name:
                continue

            # already settled with its best cost, nothing to gain
            if item["name"] in self.is_found:
                break

            cost, real_cost, flag = self.count_estimated_number(
                prev_cost,
                item
            )

            if flag == "blocked":
                break

            known = self.best_cost.get(item["name"])

            # only keep this way in when it is cheaper than the best
            # one found so far for that zone
            if known is not None and known <= real_cost:
                break

            self.best_cost[item["name"]] = real_cost
            self.came_from[item["name"]] = prev_name
            self.apply_min_heap(cost, real_cost, item, flag)
            break

    def rebuild_path(self) -> None:
        """Walk the came_from links back and store the real route."""

        names = [self.end["name"]]
        current = self.end["name"]

        while current in self.came_from:
            current = self.came_from[current]
            names.append(current)

        names.reverse()

        for name in names:
            for item in self.data:
                if item["name"] == name:
                    self.path.append(item)
                    break

    def find_shortest_path(self) -> None:
        """Find the shortest path from the start zone to the end zone."""

        self.path = []
        self.came_from = {}
        self.is_found = set()
        self.best_cost = {self.start["name"]: 0}
        self.min_heap = [(self.heuristic_only(), self.start, 0)]

        while self.min_heap:
            current_node = self.min_heap.pop(0)
            current_zone = current_node[1]
            current_name = current_zone["name"]

            # the first time a zone leaves the heap its cost is final
            if current_name in self.is_found:
                continue

            self.is_found.add(current_name)

            if current_name == self.end["name"]:
                self.total_cost = current_node[2]
                self.rebuild_path()
                return

            for neighbor in current_zone.get("neighbors", []):
                if not neighbor:
                    continue

                self.append_neighbors(
                    neighbor[0],
                    current_node[2],
                    current_name
                )

    def heuristic_only(self) -> int:
        """Return the estimated cost of the start zone.

        Returns:
            int: h(n) of the start zone, its g(n) being zero.
        """

        goal_x = int(self.end["x_coordinate"])
        goal_y = int(self.end["y_coordinate"])

        start_x = int(self.start["x_coordinate"])
        start_y = int(self.start["y_coordinate"])

        distance = abs(goal_x - start_x) + abs(goal_y - start_y)

        return -(-distance // self.span)
