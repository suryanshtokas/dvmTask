from collections import deque
from itertools import permutations
from network.models import Node, Edge
from trips.utils import find_route, find_route_cost
from .models import FareConfig, CarpoolOffer, CarpoolRequest


def get_proximity_nodes(node, max_hops=2):
    visited = set()
    visited.add(node.id)
    queue = deque()
    queue.append((node, 0))

    while queue:
        current_node, hops = queue.popleft()

        if hops >= max_hops:
            continue

        outgoing = Node.objects.filter(outgoing_edges__from_node=current_node)
        incoming = Node.objects.filter(incoming_edges__to_node=current_node)

        for neighbour in list(outgoing) + list(incoming):
            if neighbour.id not in visited:
                visited.add(neighbour.id)
                queue.append((neighbour, hops +1))

    return Node.objects.filter(id__in=visited)


def get_remaining_route(trip):
    return [
        trip_node.node for trip_node in trip.trip_nodes.filter(is_passed=False).order_by("order")
    ]


def calculate_route_cost(route):
    total = 0
    for i in range(len(route) - 1):
        cost = find_route_cost(route[i], route[i+1])
        if cost == float("inf"):
            return float("inf")
        total += cost
    return total


def optimize_route(remaining_route, passengers):
    if not passengers:
        return remaining_route
    
    start_node = remaining_route[0]
    end_node = remaining_route[-1]

    # reduce passengers to a bunch of stops
    stops = []
    for pickup, dropoff in passengers:
        stops.append(("pickup", pickup))
        stops.append(("dropoff", dropoff))

    best_route = None
    best_cost = float("inf")

    for perm in permutations(stops):
        valid = True
        for pickup, dropoff in passengers:
            pickup_idx = next((i for i, (t, n) in enumerate(perm) if t == "pickup" and n.id == pickup.id), None)
            dropoff_idx = next((i for i, (t, n) in enumerate(perm) if t == "dropoff" and n.id == dropoff.id), None)

            if pickup_idx is None or dropoff_idx is None or pickup_idx >= dropoff_idx:
                valid = False
                break

            if not valid:
                continue

            waypoints = [start_node] + [node for _, node in perm] + [end_node]

            # remove duplicates
            waypoints = [
                waypoints[i] for i in range(len(waypoints)) if i == 0 or waypoints[i].id != waypoints[i-1].id
            ]

            full_route = []
            valid_route = True
            for i in range(len(waypoints) - 1):
                segment = find_route(waypoints[i], waypoints[i+1])
                if segment is None:
                    valid_route = False
                    break
                if full_route:
                    full_route += segment[1:]
                else:
                    full_route = segment
                
            if not valid_route:
                continue

            cost = calculate_route_cost(full_route)
            if cost < best_cost:
                best_cost = cost
                best_route = full_route

    return best_route if best_route else remaining_route


def calculate_detour(trip, pickup_node, dropoff_node):
    remaining_route = get_remaining_route(trip)
    original_cost = calculate_route_cost(remaining_route)

    confirmed_offers = CarpoolOffer.objects.filter(
        trip=trip,
        status="accepted",
    ).select_related("carpool_request__pickup_node", "carpool_request__dropoff_node")

    confirmed_passengers = [
        (o.carpool_request.pickup_node, o.carpool_request.dropoff_node) for o in confirmed_offers
    ]

    all_passengers = confirmed_passengers + [(pickup_node, dropoff_node)]
    new_route = optimize_route(remaining_route, all_passengers)

    if new_route is None:
        return None, None
    
    new_cost = calculate_route_cost(new_route)
    detour = new_cost - original_cost

    return detour, new_route


def calculate_fare(new_route, confirmed_passengers, pickup_node, dropoff_node):
    config = FareConfig.objects.first()
    if not config:
        # switching to default
        unit_price = 1.00
        base_fee = 2.00
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
            p_pickup_idx = next((j for j, node in enumerate(new_route) if node.id == passenger_pickup.id), None)
            p_dropoff_idx = next((j for j, node in enumerate(new_route) if node.id == passenger_dropoff.id), None)

            if p_pickup_idx is not None and p_dropoff_idx is not None and p_pickup_idx <= i < p_dropoff_idx:
                n_i += 1
        
        fare_sum += 1/n_i
    
    fare = unit_price * fare_sum + base_fee
    return round(fare, 2)