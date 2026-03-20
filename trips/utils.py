import heapq
from network.models import Node, Edge


def find_route(start_node, end_node):
    if start_node == end_node:
        return [start_node]
    
    # priority queue for Dijkstra's algorithm
    queue = [(0, start_node.id, [start_node])]
    visited = set()

    while queue:
        cost, current_id, path = heapq.heappop(queue)

        if current_id in visited:
            continue
        visited.add(current_id)

        if current_id == end_node.id:
            return path
        
        edges = Edge.objects.filter(from_node_id=current_id).select_related("to_node")

        for edge in edges:
            if edge.to_node_id not in visited:
                heapq.heappush(queue, (
                    cost + edge.weight, edge.to_node_id, path + [edge.to_node]
                ))

    return None


def find_route_cost(start_node, end_node):
    if start_node.id == end_node.id:
        return 0
    
    queue = [(0, start_node.id)]
    visited = set()

    while queue:
        cost, current_id = heapq.heappop(queue)

        if current_id in visited:
            continue
        visited.add(current_id)

        if current_id == end_node.id:
            return cost
        
        edges = Edge.objects.filter(from_node_id=current_id).select_related("to_node")

        for edge in edges:
            if edge.to_node_id not in visited:
                heapq.heappush(queue, (cost + edge.weight, edge.to_node_id))
    
    return float("inf")