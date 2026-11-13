
# Aim: To allocate ambulances and hospital beds using DAA algorithms.

import sqlite3

from core.algorithms import (
    load_graph,
    prioritize_emergencies,
    find_nearest_ambulance,
    find_nearest_bed,
    dijkstra
)

print("Swayam Arora - 1/24/SET/BCS/349")

DB_NAME = "emergency.db"


def allocate_emergency(patient_id):

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:

        # Lock database for safe resource allocation
        cur.execute("BEGIN IMMEDIATE")

        # Get patient
        patient = cur.execute("""
            SELECT *
            FROM patients
            WHERE id = ?
        """, (patient_id,)).fetchone()

        if not patient:
            return {
                "success": False,
                "message": "Patient not found."
            }

        if patient["status"] != "Pending":
            return {
                "success": False,
                "message": "Patient is not pending."
            }

        # Load campus road network
        graph = load_graph(DB_NAME)

        # Get available ambulances
        ambulance_rows = cur.execute("""
            SELECT *
            FROM resources
            WHERE type = 'Ambulance'
            AND available = 1
        """).fetchall()

        ambulances = [dict(row) for row in ambulance_rows]

        # Get available Central Hospital beds
        bed_rows = cur.execute("""
            SELECT *
            FROM resources
            WHERE type = 'Bed'
            AND available = 1
        """).fetchall()

        beds = [dict(row) for row in bed_rows]

        if not ambulances:
            return {
                "success": False,
                "message": "No available ambulances."
            }

        if not beds:
            return {
                "success": False,
                "message": "No available hospital beds."
            }

        # Priority Queue
        pending_patients = cur.execute("""
            SELECT *
            FROM patients
            WHERE status = 'Pending'
        """).fetchall()

        ordered = prioritize_emergencies(
            [dict(row) for row in pending_patients]
        )

        if not ordered or ordered[0]["id"] != patient_id:
            return {
                "success": False,
                "message": "A higher-priority emergency must be allocated first."
            }

        # Find nearest available ambulance
        ambulance, ambulance_path, ambulance_distance = (
            find_nearest_ambulance(
                graph,
                ambulances,
                patient["location"]
            )
        )

        if ambulance is None:
            return {
                "success": False,
                "message": "No reachable ambulance."
            }

        # Find nearest available hospital bed
        bed, hospital_distance = find_nearest_bed(
            graph,
            beds,
            patient["location"]
        )

        if bed is None:
            return {
                "success": False,
                "message": "No reachable hospital bed."
            }

        # Calculate patient journey to Central Hospital
        hospital_path, verified_distance = dijkstra(
            graph,
            patient["location"],
            bed["location"]
        )

        if hospital_path is None:
            return {
                "success": False,
                "message": "Central Hospital is unreachable."
            }

        hospital_distance = verified_distance

        # Prepare complete journey
        ambulance_route = " -> ".join(ambulance_path)
        hospital_route = " -> ".join(hospital_path)

        complete_route = (
            f"Ambulance Pickup: {ambulance_route} | "
            f"Hospital Journey: {hospital_route}"
        )

        total_distance = (
            ambulance_distance + hospital_distance
        )

        # Reserve ambulance
        cur.execute("""
            UPDATE resources
            SET available = 0
            WHERE id = ?
            AND type = 'Ambulance'
            AND available = 1
        """, (ambulance["id"],))

        if cur.rowcount != 1:
            raise RuntimeError("Ambulance reservation failed.")

        # Reserve hospital bed
        cur.execute("""
            UPDATE resources
            SET available = 0
            WHERE id = ?
            AND type = 'Bed'
            AND available = 1
        """, (bed["id"],))

        if cur.rowcount != 1:
            raise RuntimeError("Hospital bed reservation failed.")

        # Update patient status
        cur.execute("""
            UPDATE patients
            SET status = 'Allocated'
            WHERE id = ?
            AND status = 'Pending'
        """, (patient_id,))

        if cur.rowcount != 1:
            raise RuntimeError("Patient status update failed.")

        # Save allocation
        cur.execute("""
            INSERT INTO allocations
            (
                patient_id,
                ambulance_id,
                bed_id,
                distance,
                route
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            patient_id,
            ambulance["id"],
            bed["id"],
            total_distance,
            complete_route
        ))

        allocation_id = cur.lastrowid

        # Save dispatch history
        cur.execute("""
            INSERT INTO dispatch_history
            (
                patient_id,
                ambulance_id,
                bed_id,
                source_location,
                destination_location,
                distance,
                algorithm,
                outcome
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            ambulance["id"],
            bed["id"],
            ambulance["location"],
            patient["location"],
            ambulance_distance,
            "Priority Queue + Dijkstra + Greedy",
            "Dispatched"
        ))

        conn.commit()

        return {
            "success": True,
            "allocation_id": allocation_id,
            "patient": patient["name"],
            "ambulance": ambulance["name"],
            "ambulance_location": ambulance["location"],
            "ambulance_route": ambulance_path,
            "ambulance_distance": ambulance_distance,
            "hospital_route": hospital_path,
            "hospital": "Central Hospital",
            "hospital_bed": bed["name"],
            "hospital_distance": hospital_distance,
            "total_distance": total_distance,
            "message": "Emergency resources allocated successfully."
        }

    except Exception as error:

        conn.rollback()

        return {
            "success": False,
            "message": str(error)
        }

    finally:
        conn.close()
