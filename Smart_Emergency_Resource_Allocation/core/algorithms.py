
# Aim: To implement DAA algorithms for smart emergency resource allocation.

import heapq
import sqlite3

print("Swayam Arora - 1/24/SET/BCS/349")


# ==========================================
# 1. PRIORITY QUEUE
# ==========================================

SEVERITY_PRIORITY = {
    "Critical": 1,
    "High": 2,
    "Moderate": 3,
    "Low": 4
}


def prioritize_emergencies(patients):

    priority_queue = []

    for patient in patients:

        priority = SEVERITY_PRIORITY.get(
            patient["severity"], 5
        )

        heapq.heappush(
            priority_queue,
            (
                priority,
                patient["id"],
                patient
            )
        )

    ordered_patients = []

    while priority_queue:

        priority, patient_id, patient = heapq.heappop(
            priority_queue
        )

        ordered_patients.append(patient)

    return ordered_patients


# ==========================================
# 2. DIJKSTRA SHORTEST PATH
# ==========================================

def dijkstra(graph, start, destination):

    distances = {
        node: float("inf")
        for node in graph
    }

    distances[start] = 0

    previous = {}

    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(
            priority_queue
        )

        if current_distance > distances[current_node]:
            continue

        if current_node == destination:
            break

        for neighbour, weight in graph[current_node]:

            new_distance = (
                current_distance + weight
            )

            if new_distance < distances[neighbour]:

                distances[neighbour] = new_distance

                previous[neighbour] = current_node

                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbour)
                )

    if distances[destination] == float("inf"):
        return None, float("inf")

    path = []
    current = destination

    while current != start:

        path.append(current)
        current = previous[current]

    path.append(start)
    path.reverse()

    return path, distances[destination]


# ==========================================
# 3. LOAD CAMPUS ROAD NETWORK
# ==========================================

def load_graph(db_name="emergency.db"):

    conn = sqlite3.connect(db_name)

    rows = conn.execute("""
        SELECT source, destination, distance
        FROM route_edges
    """).fetchall()

    conn.close()

    graph = {}

    for source, destination, distance in rows:

        graph.setdefault(source, [])
        graph.setdefault(destination, [])

        graph[source].append(
            (destination, distance)
        )

    return graph


# ==========================================
# 4. GREEDY AMBULANCE SELECTION
# ==========================================

def find_nearest_ambulance(
    graph,
    ambulances,
    patient_location
):

    best_ambulance = None
    best_path = None
    shortest_distance = float("inf")

    for ambulance in ambulances:

        path, distance = dijkstra(
            graph,
            ambulance["location"],
            patient_location
        )

        if path is not None and distance < shortest_distance:

            shortest_distance = distance
            best_ambulance = ambulance
            best_path = path

    return (
        best_ambulance,
        best_path,
        shortest_distance
    )


# ==========================================
# 5. GREEDY HOSPITAL BED SELECTION
# ==========================================

def find_nearest_bed(
    graph,
    beds,
    patient_location
):

    best_bed = None
    shortest_distance = float("inf")

    for bed in beds:

        path, distance = dijkstra(
            graph,
            patient_location,
            bed["location"]
        )

        if path is not None and distance < shortest_distance:

            shortest_distance = distance
            best_bed = bed

    return best_bed, shortest_distance


# ==========================================
# 6. ALGORITHM TEST
# ==========================================

if __name__ == "__main__":

    graph = load_graph()

    path, distance = dijkstra(
        graph,
        "A Block",
        "T Block"
    )

    print("\nDIJKSTRA ALGORITHM RESULT")
    print("Shortest Route:", path)
    print("Distance:", distance, "km")

