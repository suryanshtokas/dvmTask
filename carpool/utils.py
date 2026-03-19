from collections import deque
from network.models import Node
from .models import FareConfig


def get_proximity_nodes(node, max_hops=2):
    visited = set()
    visited.add(node.id)
    queue = deque()
    queue.append((node, 0))

    while queue:
        current_node, hops = queue.popleft()

        if hops >= max_hops:
            continue
            
        # move forward
        outgoing = Node.objects.filter(incoming_edges__from_node=current_node)
        # move backward
        incoming = Node.objects.filter(outgoing_edges__to_node=current_node)

        for neighbour in list(outgoing) + list(incoming):
            if neighbour.id not in visited:
                visited.add(neighbour.id)
                queue.append((neighbour, hops+1))
        
    return Node.objects.filter(id__in=visited)


def get_remaining_route(trip):
    return [
        trip_node.node for trip_node in trip.trip_nodes.filter(is_passed=False).order_by("order")
    ]

def get_route_length(route):
    return max(0, len(route) - 1)


def insert_passenger_into_route(route, pickup_node, dropoff_node):
    best_route = None
    best_length = float("inf")

    for i in range(len(route)):
        for j in range(i+1, len(route)+1):
            new_route = route[:i] + [pickup_node] + route[i:j] + [dropoff_node] + route[j:]
            # removing duplicates
            seen = set()
            unique_route = []
            for node in new_route:
                if node.id not in seen:
                    seen.add(node.id)
                    unique_route.append(node)
            
            length = get_route_length(unique_route)
            if length < best_length:
                best_length = length
                best_route = unique_route
    
    return best_route


def calculate_detour(trip, pickup_node, dropoff_node):
    remaining_route = get_remaining_route(trip)
    original_length = get_route_length(remaining_route)

    new_route = insert_passenger_into_route(remaining_route, pickup_node, dropoff_node)
    if new_route is None:
        return None, None
    
    new_length = get_route_length(new_route)
    detour_length = new_length - original_length

    return detour_length, new_route

def calculate_fare(new_route, confirmed_passengers, pickup_node, dropoff_node):
    config = FareConfig.objects.first()
    if not config:
        raise ValueError("Fare configuration not found.")
    else:
        unit_price = float(config.unit_price)
        base_fee = float(config.base_fee)
    
    try:
        pickup_index = next(i for i, node in enumerate(new_route) if node.id == pickup_node.id)
        dropoff_index = next(i for i, node in enumerate(new_route) if node.id == dropoff_node.id)
    except StopIteration:
        return None
    
    fare_sum = 0

    for i in range(pickup_index, dropoff_index):
        n_i = 1
        for passenger_pickup, passenger_dropoff in confirmed_passengers:
            p_pickup_index = next((j for j, n in enumerate(new_route) if n.id == passenger_pickup.id), None)
            p_dropoff_index = next((j for j, n in enumerate(new_route) if n.id == passenger_dropoff.id), None)
            if p_pickup_index is not None and p_dropoff_index is not None:
                if p_pickup_index <= i < p_dropoff_index:
                    n_i += 1
        fare_sum += 1/n_i

    fare = unit_price * fare_sum + base_fee 
    return round(fare, 2)