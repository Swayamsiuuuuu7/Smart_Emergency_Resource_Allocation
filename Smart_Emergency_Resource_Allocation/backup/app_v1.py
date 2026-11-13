
# Aim: To develop a Smart Emergency Resource Allocation System using DAA algorithms.
import streamlit as st
import sqlite3
import pandas as pd
import heapq
import time
import json
from collections import defaultdict


# DATABASE SETUP
DB_NAME = "emergency.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

def initialize_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            emergency TEXT,
            severity TEXT,
            location TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            location TEXT,
            available INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            ambulance_id INTEGER,
            bed_id INTEGER,
            distance REAL,
            route TEXT,
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("SELECT COUNT(*) FROM resources")
    if cur.fetchone()[0] == 0:
        resources = [
            ("Ambulance 1", "Ambulance", "Central"),
            ("Ambulance 2", "Ambulance", "North"),
            ("Ambulance 3", "Ambulance", "South"),
            ("Central Hospital Bed", "Bed", "Central"),
            ("North Hospital Bed", "Bed", "North"),
            ("South Hospital Bed", "Bed", "South")
        ]
        cur.executemany(
            "INSERT INTO resources (name, type, location) VALUES (?, ?, ?)",
            resources
        )

    conn.commit()
    conn.close()


# ROAD NETWORK
GRAPH = {
    "Central": {"North": 4, "South": 5, "East": 3, "West": 6},
    "North": {"Central": 4, "East": 2},
    "South": {"Central": 5, "West": 3},
    "East": {"Central": 3, "North": 2},
    "West": {"Central": 6, "South": 3}
}

# DIJKSTRA'S SHORTEST PATH ALGORITHM
def dijkstra(start, end):
    distances = {node: float("inf") for node in GRAPH}
    distances[start] = 0

    previous = {}
    pq = [(0, start)]

    while pq:
        current_distance, current = heapq.heappop(pq)

        if current_distance > distances[current]:
            continue

        if current == end:
            break

        for neighbor, weight in GRAPH[current].items():
            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(pq, (new_distance, neighbor))

    if distances[end] == float("inf"):
        return float("inf"), []

    path = []
    current = end

    while current != start:
        path.append(current)
        current = previous[current]

    path.append(start)
    path.reverse()

    return distances[end], path


# PATIENT PRIORITY QUEUE
PRIORITY = {
    "Critical": 4,
    "High": 3,
    "Moderate": 2,
    "Low": 1
}

def get_priority_queue():
    conn = connect_db()
    patients = conn.execute("""
        SELECT id, name, severity, location
        FROM patients
        WHERE status = 'Pending'
    """).fetchall()
    conn.close()

    pq = []

    for patient in patients:
        priority = PRIORITY[patient[2]]
        heapq.heappush(
            pq, (-priority, patient[0], patient)
        )

    return pq


# GREEDY RESOURCE ALLOCATION
def allocate_resource():
    pq = get_priority_queue()

    if not pq:
        return "No pending patients."

    conn = connect_db()
    cur = conn.cursor()

    # Select highest-priority patient
    _, _, patient = heapq.heappop(pq)

    patient_id, name, severity, location = patient

    ambulances = cur.execute("""
        SELECT id, name, location
        FROM resources
        WHERE type = 'Ambulance' AND available = 1
    """).fetchall()

    beds = cur.execute("""
        SELECT id, name, location
        FROM resources
        WHERE type = 'Bed' AND available = 1
    """).fetchall()

    if not ambulances or not beds:
        conn.close()
        return "No ambulance or hospital bed available."

    best = None
    min_distance = float("inf")

    # Find the best available ambulance and hospital combination
    for ambulance in ambulances:
        for bed in beds:

            d1, route1 = dijkstra(ambulance[2], location)
            d2, route2 = dijkstra(location, bed[2])

            total_distance = d1 + d2

            if total_distance < min_distance:
                min_distance = total_distance
                best = (
                    ambulance, bed,
                    route1 + route2[1:]
                )

    if best is None or min_distance == float("inf"):
        conn.close()
        return "No valid route available."

    ambulance, bed, route = best

    cur.execute(
        "UPDATE resources SET available = 0 WHERE id = ?",
        (ambulance[0],)
    )

    cur.execute(
        "UPDATE resources SET available = 0 WHERE id = ?",
        (bed[0],)
    )

    cur.execute("""
        UPDATE patients
        SET status = 'Allocated'
        WHERE id = ?
    """, (patient_id,))

    cur.execute("""
        INSERT INTO allocations
        (patient_id, ambulance_id, bed_id, distance, route)
        VALUES (?, ?, ?, ?, ?)
    """, (
        patient_id,
        ambulance[0],
        bed[0],
        min_distance,
        json.dumps(route)
    ))

    conn.commit()
    conn.close()

    return (
        f"Successfully allocated resources to {name}!\n"
        f"Ambulance: {ambulance[1]}\n"
        f"Hospital: {bed[1]}\n"
        f"Route: {' → '.join(route)}\n"
        f"Total distance: {min_distance} km"
    )


# STREAMLIT APPLICATION
st.set_page_config(
    page_title="Emergency Resource Allocation",
    page_icon="🚑",
    layout="wide"
)

initialize_database()

st.title("🚑 Smart Emergency Resource Allocation System")
st.caption("DAA Project | Educational Emergency Allocation Simulation")

st.info(
    "This application demonstrates algorithm-based resource "
    "allocation. It is an educational simulation, not a real "
    "emergency dispatch system."
)

# DASHBOARD
conn = connect_db()

total_patients = conn.execute(
    "SELECT COUNT(*) FROM patients"
).fetchone()[0]

pending = conn.execute(
    "SELECT COUNT(*) FROM patients WHERE status='Pending'"
).fetchone()[0]

available_ambulances = conn.execute("""
    SELECT COUNT(*) FROM resources
    WHERE type='Ambulance' AND available=1
""").fetchone()[0]

available_beds = conn.execute("""
    SELECT COUNT(*) FROM resources
    WHERE type='Bed' AND available=1
""").fetchone()[0]

conn.close()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Patients", total_patients)
c2.metric("Pending Requests", pending)
c3.metric("Available Ambulances", available_ambulances)
c4.metric("Available Beds", available_beds)

st.divider()

# NAVIGATION TABS
tab1, tab2, tab3, tab4 = st.tabs([
    "Register Patient",
    "Allocate Resources",
    "Allocation History",
    "Algorithm Analysis"
])

# TAB 1: PATIENT REGISTRATION
with tab1:
    st.subheader("Register Emergency Patient")

    with st.form("patient_form"):
        name = st.text_input("Patient Name")

        emergency = st.selectbox(
            "Emergency Type",
            ["Accident", "Heart Attack", "Burn Injury",
             "Breathing Problem", "Other"]
        )

        severity = st.selectbox(
            "Emergency Severity",
            ["Critical", "High", "Moderate", "Low"]
        )

        location = st.selectbox(
            "Patient Location",
            list(GRAPH.keys())
        )

        submit = st.form_submit_button("Register Patient")

        if submit:
            if name.strip():
                conn = connect_db()
                conn.execute("""
                    INSERT INTO patients
                    (name, emergency, severity, location)
                    VALUES (?, ?, ?, ?)
                """, (name.strip(), emergency, severity, location))
                conn.commit()
                conn.close()

                st.success("Patient registered successfully!")
            else:
                st.error("Please enter the patient name.")

# TAB 2: RESOURCE ALLOCATION
with tab2:
    st.subheader("Emergency Resource Allocation")

    st.write(
        "The system selects the most critical pending patient "
        "and assigns the nearest available ambulance and hospital bed."
    )

    if st.button("Allocate Next Emergency", type="primary"):
        start_time = time.perf_counter()
        result = allocate_resource()
        end_time = time.perf_counter()

        st.success(result)
        st.caption(
            f"Allocation execution time: "
            f"{(end_time - start_time) * 1000:.4f} ms"
        )

    st.subheader("Current Patient Queue")

    conn = connect_db()
    df = pd.read_sql_query("""
        SELECT id, name, emergency, severity, location, status
        FROM patients
        ORDER BY
        CASE severity
            WHEN 'Critical' THEN 1
            WHEN 'High' THEN 2
            WHEN 'Moderate' THEN 3
            WHEN 'Low' THEN 4
        END,
        id ASC
    """, conn)
    conn.close()

    st.dataframe(df, use_container_width=True, hide_index=True)

# TAB 3: ALLOCATION HISTORY
with tab3:
    st.subheader("Resource Allocation History")

    conn = connect_db()

    history = pd.read_sql_query("""
        SELECT
            p.name AS Patient,
            p.severity AS Severity,
            a.name AS Ambulance,
            b.name AS Hospital,
            al.distance AS Distance_KM,
            al.route AS Route,
            al.allocated_at AS Allocation_Time
        FROM allocations al
        JOIN patients p ON al.patient_id = p.id
        JOIN resources a ON al.ambulance_id = a.id
        JOIN resources b ON al.bed_id = b.id
        ORDER BY al.id DESC
    """, conn)

    conn.close()

    if not history.empty:
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No allocations have been made yet.")

# TAB 4: ALGORITHM ANALYSIS
with tab4:
    st.subheader("DAA Algorithm Analysis")

    analysis = pd.DataFrame({
        "Algorithm": [
            "Priority Queue",
            "Greedy Allocation",
            "Dijkstra's Algorithm",
            "Sorting"
        ],
        "Purpose": [
            "Patient prioritization",
            "Resource assignment",
            "Shortest route",
            "Ranking patients"
        ],
        "Time Complexity": [
            "O(log n) per insertion/removal",
            "O(A × B × (V + E) log V)",
            "O((V + E) log V)",
            "O(n log n)"
        ]
    })

    st.table(analysis)

    st.write("### Road Network")

    st.write(
        "Central, North, South, East and West represent "
        "different locations in our simulated city."
    )

    st.write("### Dijkstra's Algorithm Example")

    start = st.selectbox(
        "Starting Location",
        list(GRAPH.keys()),
        key="route_start"
    )

    end = st.selectbox(
        "Destination",
        list(GRAPH.keys()),
        index=1,
        key="route_end"
    )

    if st.button("Find Shortest Route"):
        distance, route = dijkstra(start, end)

        if distance == float("inf"):
            st.error("No route found.")
        else:
            st.success(f"Shortest Distance: {distance} km")
            st.write("Route:", " → ".join(route))

