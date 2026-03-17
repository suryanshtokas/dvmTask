from collections import deque
from network.models import Node


def find_shortest_route(start_node, end_node):
    if start_node == end_node:
        return [start_node]
    
    queue = deque()
    queue.append((start_node, [start_node]))

    visited = set()
    visited.add(start_node.id)
    
    while queue:
        current_node, path = queue.popleft()

        neighbours = Node.objects.filter(incoming_edges__from_node=current_node)

        for neighbour in neighbours:
            if neighbour.id in visited:
                continue
            
            new_path = path + [neighbour]

            if neighbour == end_node:
                return new_path
            
            visited.add(neighbour.id)
            queue.append((neighbour, new_path))
        
    return None  