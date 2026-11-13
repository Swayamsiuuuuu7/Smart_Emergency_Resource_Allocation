
# Aim: To develop an advanced Smart Emergency Resource Allocation System.

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

from core.allocation import allocate_emergency

print("Swayam Arora - 1/24/SET/BCS/349")

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Emergency Response Command",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "emergency.db"

LOCATIONS = [
    "A Block",
    "B Block",
    "C Block",
    "G Block",
    "T Block"
]

HOSPITAL = "Central Hospital"

NAVIGATION = [
    "Overview",
    "Patient Management",
    "Ambulance Management",
    "Hospital Management",
    "Smart Allocation",
    "Reports & History"
]

# ==================================================
# LIGHT THEME
# ==================================================

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FB;
    color: #243247;
}

[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

[data-testid="stSidebar"] * {
    color: #243247;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px;
    min-height: 125px;
    box-shadow: 0 2px 8px rgba(30,50,80,0.04);
}

.metric-label {
    color: #718096;
    font-size: 14px;
}

.metric-value {
    color: #172B4D;
    font-size: 29px;
    font-weight: 700;
    margin-top: 8px;
}

.metric-note {
    color: #159B78;
    font-size: 12px;
    margin-top: 5px;
}

[data-testid="stMetricValue"] {
    color: #172B4D;
}

[data-testid="stMetricLabel"] {
    color: #718096;
}

div.stButton > button[kind="primary"] {
    background-color: #DC3636;
    border-color: #DC3636;
    color: white;
    font-weight: 600;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #B92727;
    border-color: #B92727;
}

.emergency-box {
    background: #FFF0F0;
    border: 1px solid #F5CACA;
    border-radius: 12px;
    padding: 18px;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# DATABASE FUNCTIONS
# ==================================================

def connect_db():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def get_columns(cur, table):
    return [
        row["name"]
        for row in cur.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]


def initialize_database():

    conn = connect_db()
    cur = conn.cursor()

    try:
        # Patients
        cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                emergency TEXT,
                severity TEXT,
                location TEXT,
                status TEXT DEFAULT 'Pending',
                phone TEXT,
                details TEXT
            )
        """)

        # Resources
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                location TEXT,
                available INTEGER DEFAULT 1
            )
        """)

        # Add optional patient columns safely
        patient_columns = get_columns(cur, "patients")

        if "phone" not in patient_columns:
            cur.execute(
                "ALTER TABLE patients ADD COLUMN phone TEXT"
            )

        if "details" not in patient_columns:
            cur.execute(
                "ALTER TABLE patients ADD COLUMN details TEXT"
            )

        # Allocation table: matches core/allocation.py
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

        # Safely add allocation columns if an older table exists
        allocation_columns = get_columns(cur, "allocations")

        for column, definition in [
            ("distance", "REAL"),
            ("route", "TEXT")
        ]:
            if column not in allocation_columns:
                cur.execute(
                    f"ALTER TABLE allocations ADD COLUMN {column} {definition}"
                )

        # Dispatch history
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dispatch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                ambulance_id INTEGER,
                bed_id INTEGER,
                source_location TEXT,
                destination_location TEXT,
                distance REAL,
                algorithm TEXT,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Hospital
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                location TEXT,
                total_beds INTEGER
            )
        """)

        cur.execute("""
            INSERT INTO hospitals (name, location, total_beds)
            SELECT ?, ?, 100
            WHERE NOT EXISTS (
                SELECT 1 FROM hospitals WHERE name = ?
            )
        """, (HOSPITAL, HOSPITAL, HOSPITAL))

        # Road network: preserve existing four-column schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS route_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                destination TEXT,
                distance REAL
            )
        """)

        # Only seed routes when the network is empty
        edge_count = cur.execute(
            "SELECT COUNT(*) FROM route_edges"
        ).fetchone()[0]

        if edge_count == 0:

            routes = [
                ("A Block", HOSPITAL, 1.2),
                ("B Block", HOSPITAL, 1.0),
                ("C Block", HOSPITAL, 0.8),
                ("G Block", HOSPITAL, 1.1),
                ("T Block", HOSPITAL, 1.5)
            ]

            for source, destination, distance in routes:

                cur.execute("""
                    INSERT INTO route_edges
                    (source, destination, distance)
                    VALUES (?, ?, ?)
                """, (source, destination, distance))

                cur.execute("""
                    INSERT INTO route_edges
                    (source, destination, distance)
                    VALUES (?, ?, ?)
                """, (destination, source, distance))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_data(query, params=()):

    conn = connect_db()

    try:
        return pd.read_sql_query(
            query,
            conn,
            params=params
        )

    except Exception as error:
        st.error(f"Database error: {error}")
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# RESOURCE INITIALIZATION
# ==================================================

def initialize_resources():

    conn = connect_db()
    cur = conn.cursor()

    try:
        ambulance_count = cur.execute("""
            SELECT COUNT(*) FROM resources
            WHERE type = 'Ambulance'
        """).fetchone()[0]

        locations = LOCATIONS

        for i in range(ambulance_count, 10):
            cur.execute("""
                INSERT INTO resources
                (name, type, location, available)
                VALUES (?, 'Ambulance', ?, 1)
            """, (
                f"Ambulance {i + 1}",
                locations[i % 5]
            ))

        bed_count = cur.execute("""
            SELECT COUNT(*) FROM resources
            WHERE type = 'Bed'
        """).fetchone()[0]

        for i in range(bed_count, 100):
            cur.execute("""
                INSERT INTO resources
                (name, type, location, available)
                VALUES (?, 'Bed', ?, 1)
            """, (
                f"Central Hospital Bed {i + 1}",
                HOSPITAL
            ))

        # Ensure existing ambulances use the five campus blocks
        ambulances = cur.execute("""
            SELECT id FROM resources
            WHERE type = 'Ambulance'
            ORDER BY id
        """).fetchall()

        for i, ambulance in enumerate(ambulances):
            cur.execute("""
                UPDATE resources
                SET location = ?
                WHERE id = ?
            """, (
                locations[i % 5],
                ambulance["id"]
            ))

        # Keep existing bed availability unchanged
        # and associate all beds with Central Hospital
        beds = cur.execute("""
            SELECT id FROM resources
            WHERE type = 'Bed'
            ORDER BY id
        """).fetchall()

        for i, bed in enumerate(beds, 1):
            cur.execute("""
                UPDATE resources
                SET name = ?, location = ?
                WHERE id = ?
            """, (
                f"Central Hospital Bed {i}",
                HOSPITAL,
                bed["id"]
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


initialize_database()
initialize_resources()


# ==================================================
# SESSION STATE AND NAVIGATION
# ==================================================

if "active_page" not in st.session_state:
    st.session_state.active_page = "Overview"

if "pending_dispatch_id" not in st.session_state:
    st.session_state.pending_dispatch_id = None

if "last_dispatch_result" not in st.session_state:
    st.session_state.last_dispatch_result = None


def set_page(selected_page):
    st.session_state.active_page = selected_page


# ==================================================
# DISPATCH FUNCTION
# ==================================================

def dispatch_patient(patient_id):

    with st.spinner(
        "Finding nearest ambulance and hospital bed..."
    ):

        result = allocate_emergency(int(patient_id))

    if result["success"]:
        st.session_state.last_dispatch_result = result
        st.session_state.pending_dispatch_id = None
        st.success("Emergency resources allocated successfully!")

    else:
        st.error(result["message"])


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown("## 🚑 ER COMMAND")
    st.caption("Emergency Response System")

    st.divider()

    st.button(
        "🚨 NEW EMERGENCY",
        type="primary",
        use_container_width=True,
        on_click=set_page,
        args=("New Emergency",)
    )

    st.divider()

    st.markdown("### MAIN MENU")

    for item in NAVIGATION:

        is_active = (
            st.session_state.active_page == item
        )

        st.button(
            ("● " if is_active else "○ ") + item,
            key="nav_" + item,
            use_container_width=True,
            type="primary" if is_active else "secondary",
            on_click=set_page,
            args=(item,)
        )

    st.divider()

    st.markdown("### SYSTEM STATUS")

    st.success("System Online")
    st.caption("Central Hospital")
    st.caption("DAA Project | 2026")


page = st.session_state.active_page


# ==================================================
# DATABASE STATISTICS
# ==================================================

patients = get_data("SELECT * FROM patients")
resources = get_data("SELECT * FROM resources")
allocations = get_data("SELECT * FROM allocations")
dispatches = get_data("SELECT * FROM dispatch_history")

if not patients.empty:

    total_patients = len(patients)

    pending = len(
        patients[patients["status"] == "Pending"]
    )

    allocated = len(
        patients[patients["status"] == "Allocated"]
    )

    critical = len(
        patients[patients["severity"] == "Critical"]
    )

else:
    total_patients = pending = allocated = critical = 0


if not resources.empty:

    ambulances = resources[
        resources["type"] == "Ambulance"
    ]

    beds = resources[
        resources["type"] == "Bed"
    ]

    available_ambulances = int(
        ambulances["available"].sum()
    )

    available_beds = int(
        beds["available"].sum()
    )

    total_ambulances = len(ambulances)
    total_beds = len(beds)

else:
    available_ambulances = available_beds = 0
    total_ambulances = total_beds = 0


# ==================================================
# NEW EMERGENCY SCREEN
# ==================================================

if page == "New Emergency":

    st.title("🚨 Emergency Dispatch Center")

    st.caption(
        "Register a patient and initiate an emergency response."
    )

    st.warning(
        "Educational simulation only. "
        "This application is not a real emergency service."
    )

    st.subheader("Patient Information")

    with st.form("quick_emergency"):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Patient Full Name *",
                placeholder="Enter patient name"
            )

            phone = st.text_input(
                "Contact Number",
                placeholder="Enter contact number"
            )

            emergency = st.selectbox(
                "Emergency Type",
                [
                    "Road Accident",
                    "Heart Attack",
                    "Breathing Problem",
                    "Burn Injury",
                    "Stroke",
                    "Fracture",
                    "Other"
                ]
            )

        with col2:

            severity = st.selectbox(
                "Emergency Severity",
                [
                    "Critical",
                    "High",
                    "Moderate",
                    "Low"
                ]
            )

            location = st.selectbox(
                "Patient Location",
                LOCATIONS
            )

            st.caption(
                "Select the block where the patient is located."
            )

        details = st.text_area(
            "Additional Emergency Information",
            placeholder="Enter additional details..."
        )

        st.divider()

        priority_values = {
            "Critical": 4,
            "High": 3,
            "Moderate": 2,
            "Low": 1
        }

        st.write("### Emergency Priority")

        p1, p2 = st.columns(2)

        p1.metric(
            "Priority Score",
            priority_values[severity]
        )

        p2.metric(
            "Emergency Level",
            severity
        )

        submitted = st.form_submit_button(
            "REGISTER EMERGENCY",
            type="primary",
            use_container_width=True
        )

    if submitted:

        if not name.strip():
            st.error("Please enter the patient's name.")

        elif phone and not phone.isdigit():
            st.error("Contact number must contain digits only.")

        else:

            conn = connect_db()

            try:
                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO patients
                    (
                        name,
                        emergency,
                        severity,
                        location,
                        status,
                        phone,
                        details
                    )
                    VALUES (?, ?, ?, ?, 'Pending', ?, ?)
                """, (
                    name.strip(),
                    emergency,
                    severity,
                    location,
                    phone,
                    details
                ))

                patient_id = cur.lastrowid
                conn.commit()

                st.session_state.pending_dispatch_id = patient_id
                st.session_state.last_dispatch_result = None

                st.success(
                    f"Emergency registered! Patient ID: {patient_id}"
                )

            except Exception as error:
                conn.rollback()
                st.error(str(error))

            finally:
                conn.close()

    # DISPATCH PANEL

    st.divider()
    st.subheader("🚑 Emergency Dispatch")

    pending_dispatch_id = st.session_state.pending_dispatch_id

    if pending_dispatch_id:

        dispatch_patient_data = get_data(
            "SELECT * FROM patients WHERE id = ?",
            (pending_dispatch_id,)
        )

        if not dispatch_patient_data.empty:

            patient = dispatch_patient_data.iloc[0]

            if patient["status"] == "Pending":

                st.info(
                    f"Patient: {patient['name']} | "
                    f"Severity: {patient['severity']} | "
                    f"Location: {patient['location']}"
                )

                if st.button(
                    "🚑 DISPATCH NOW",
                    type="primary",
                    use_container_width=True
                ):
                    dispatch_patient(pending_dispatch_id)
                    st.rerun()

            else:
                st.warning("This patient is no longer pending.")
                st.session_state.pending_dispatch_id = None

    else:
        st.caption(
            "Register a new emergency to start dispatch."
        )

    # DISPATCH CONFIRMATION

    result = st.session_state.last_dispatch_result

    if result:

        st.divider()

        st.success(
            "Emergency resources allocated successfully!"
        )

        st.subheader("Dispatch Confirmation")

        d1, d2, d3 = st.columns(3)

        d1.metric(
            "Assigned Ambulance",
            result["ambulance"]
        )

        d2.metric(
            "Hospital Bed",
            result["hospital_bed"]
        )

        d3.metric(
            "Total Journey",
            f"{result['total_distance']:.2f} km"
        )

        st.markdown("### Ambulance Information")

        st.write(
            "**Ambulance Starting Location:**",
            result["ambulance_location"]
        )

        st.write(
            "**Pickup Route:**",
            " → ".join(result["ambulance_route"])
        )

        st.write(
            "**Pickup Distance:**",
            f"{result['ambulance_distance']:.2f} km"
        )

        st.divider()

        st.markdown("### Hospital Information")

        st.write("**Destination:**", result["hospital"])

        st.write("**Assigned Bed:**", result["hospital_bed"])

        st.write(
            "**Hospital Route:**",
            " → ".join(result["hospital_route"])
        )

        st.write(
            "**Hospital Distance:**",
            f"{result['hospital_distance']:.2f} km"
        )

        st.write(
            "**Total Journey Distance:**",
            f"{result['total_distance']:.2f} km"
        )

        if st.button("Clear Dispatch Confirmation"):
            st.session_state.last_dispatch_result = None
            st.rerun()


# ==================================================
# OVERVIEW DASHBOARD
# ==================================================

elif page == "Overview":

    st.title("Emergency Response Dashboard")

    st.caption(
        "Monitor emergencies, manage resources "
        "and optimize response operations."
    )

    st.divider()

    st.subheader("Operational Overview")

    c1, c2, c3, c4 = st.columns(4)

    cards = [
        (c1, "Total Emergencies", total_patients, "All registered cases"),
        (c2, "Critical Patients", critical, "Require urgent attention"),
        (
            c3,
            "Available Ambulances",
            f"{available_ambulances}/{total_ambulances}",
            "Fleet availability"
        ),
        (
            c4,
            "Available Hospital Beds",
            f"{available_beds}/{total_beds}",
            "Hospital capacity"
        )
    ]

    for col, label, value, note in cards:

        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-note">{note}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # EMERGENCY CHARTS

    left, right = st.columns(2)

    with left:

        st.markdown("### Emergency Severity Distribution")

        if not patients.empty:

            severity_data = (
                patients["severity"]
                .value_counts()
                .reindex(
                    ["Critical", "High", "Moderate", "Low"],
                    fill_value=0
                )
                .rename_axis("Severity")
                .reset_index(name="Patients")
            )

            fig = px.pie(
                severity_data,
                names="Severity",
                values="Patients",
                hole=0.65,
                color="Severity",
                color_discrete_map={
                    "Critical": "#E05252",
                    "High": "#F39C52",
                    "Moderate": "#E8C547",
                    "Low": "#36A98C"
                }
            )

            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(t=20, b=20, l=20, r=20),
                legend_title_text=""
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No emergency records available yet.")

    with right:

        st.markdown("### Patient Status")

        status_data = pd.DataFrame({
            "Status": ["Pending", "Allocated"],
            "Patients": [pending, allocated]
        })

        fig = px.bar(
            status_data,
            x="Status",
            y="Patients",
            color="Status",
            color_discrete_map={
                "Pending": "#F0A44B",
                "Allocated": "#329C82"
            },
            text="Patients"
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            yaxis_title="Number of Patients"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # RESOURCE UTILIZATION

    st.subheader("Resource Utilization")

    r1, r2 = st.columns(2)

    with r1:

        st.markdown("**Ambulance Fleet**")

        ambulance_usage = (
            (total_ambulances - available_ambulances)
            / total_ambulances * 100
            if total_ambulances else 0
        )

        st.progress(int(ambulance_usage))

        st.write(
            f"{ambulance_usage:.1f}% currently allocated"
        )

    with r2:

        st.markdown("**Hospital Beds**")

        bed_usage = (
            (total_beds - available_beds)
            / total_beds * 100
            if total_beds else 0
        )

        st.progress(int(bed_usage))

        st.write(
            f"{bed_usage:.1f}% currently occupied"
        )

    st.divider()

    # RECENT ACTIVITY

    st.subheader("Recent Emergency Activity")

    if not patients.empty:

        recent = (
            patients
            .sort_values("id", ascending=False)
            .head(8)
        )

        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No emergency activity recorded.")


# ==================================================
# PATIENT MANAGEMENT
# ==================================================

elif page == "Patient Management":

    st.title("Patient Management")

    st.caption("View and manage registered emergency patients.")

    if not patients.empty:

        st.dataframe(
            patients.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        patient_id = st.selectbox(
            "Select Patient ID",
            patients["id"].tolist()
        )

        selected = patients[
            patients["id"] == patient_id
        ].iloc[0]

        st.subheader("Patient Details")

        st.write("**Name:**", selected["name"])
        st.write("**Emergency:**", selected["emergency"])
        st.write("**Severity:**", selected["severity"])
        st.write("**Location:**", selected["location"])
        st.write("**Status:**", selected["status"])

        if selected["status"] == "Pending":

            if st.button(
                "🚑 Dispatch Selected Patient",
                type="primary"
            ):

                result = allocate_emergency(int(patient_id))

                if result["success"]:

                    st.success(
                        f"Allocated {result['ambulance']} "
                        f"and {result['hospital_bed']}."
                    )

                    st.write(
                        "Pickup Route:",
                        " → ".join(result["ambulance_route"])
                    )

                    st.write(
                        "Hospital Route:",
                        " → ".join(result["hospital_route"])
                    )

                    st.write(
                        "Total Distance:",
                        f"{result['total_distance']:.2f} km"
                    )

                    st.rerun()

                else:
                    st.error(result["message"])

    else:
        st.info("No patients registered yet.")


# ==================================================
# AMBULANCE MANAGEMENT
# ==================================================

elif page == "Ambulance Management":

    st.title("🚑 Ambulance Management")

    st.caption("Monitor ambulance fleet availability.")

    ambulance_data = resources[
        resources["type"] == "Ambulance"
    ].copy() if not resources.empty else pd.DataFrame()

    if not ambulance_data.empty:

        a1, a2, a3 = st.columns(3)

        a1.metric("Total Ambulances", len(ambulance_data))

        a2.metric(
            "Available",
            int(ambulance_data["available"].sum())
        )

        a3.metric(
            "Dispatched",
            len(ambulance_data) -
            int(ambulance_data["available"].sum())
        )

        st.divider()

        st.subheader("Ambulance Fleet")

        st.dataframe(
            ambulance_data,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("Block-wise Ambulance Distribution")

        distribution = (
            ambulance_data.groupby("location")
            .size()
            .reset_index(name="Ambulances")
        )

        fig = px.bar(
            distribution,
            x="location",
            y="Ambulances",
            text="Ambulances"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No ambulances found.")


# ==================================================
# HOSPITAL MANAGEMENT
# ==================================================

elif page == "Hospital Management":

    st.title("🏥 Hospital Management")

    st.caption("Monitor Central Hospital bed availability.")

    bed_data = resources[
        resources["type"] == "Bed"
    ].copy() if not resources.empty else pd.DataFrame()

    st.subheader("Central Hospital")

    st.info("All emergency patients are transported to Central Hospital.")

    if not bed_data.empty:

        b1, b2, b3 = st.columns(3)

        b1.metric("Total Beds", len(bed_data))

        b2.metric(
            "Available Beds",
            int(bed_data["available"].sum())
        )

        b3.metric(
            "Occupied Beds",
            len(bed_data) -
            int(bed_data["available"].sum())
        )

        st.divider()

        st.subheader("Hospital Bed Inventory")

        st.dataframe(
            bed_data,
            use_container_width=True,
            hide_index=True
        )

        bed_usage = (
            (len(bed_data) - int(bed_data["available"].sum()))
            / len(bed_data) * 100
        )

        st.subheader("Bed Occupancy")

        st.progress(int(bed_usage))

        st.write(f"{bed_usage:.1f}% beds occupied")

    else:
        st.info("No hospital beds found.")


# ==================================================
# SMART ALLOCATION
# ==================================================

elif page == "Smart Allocation":

    st.title("🧠 Smart Resource Allocation")

    st.caption(
        "Priority Queue + Dijkstra + Greedy Allocation"
    )

    st.subheader("Pending Emergencies")

    if not patients.empty:

        pending_data = patients[
            patients["status"] == "Pending"
        ].copy()

        if not pending_data.empty:

            priority_order = {
                "Critical": 1,
                "High": 2,
                "Moderate": 3,
                "Low": 4
            }

            pending_data["Priority"] = (
                pending_data["severity"]
                .map(priority_order)
            )

            pending_data = pending_data.sort_values(
                ["Priority", "id"]
            )

            st.dataframe(
                pending_data,
                use_container_width=True,
                hide_index=True
            )

            st.info(
                "Critical emergencies are processed before "
                "High, Moderate and Low emergencies."
            )

            st.divider()

            patient_id = st.selectbox(
                "Select Pending Patient",
                pending_data["id"].tolist(),
                format_func=lambda x: (
                    f"ID {x} - "
                    f"{pending_data.loc[pending_data['id'] == x, 'name'].iloc[0]}"
                )
            )

            if st.button(
                "ALLOCATE RESOURCES",
                type="primary",
                use_container_width=True
            ):

                result = allocate_emergency(int(patient_id))

                if result["success"]:

                    st.success(result["message"])

                    st.subheader("Allocation Result")

                    st.write("**Ambulance:**", result["ambulance"])

                    st.write(
                        "**Ambulance Location:**",
                        result["ambulance_location"]
                    )

                    st.write(
                        "**Pickup Route:**",
                        " → ".join(result["ambulance_route"])
                    )

                    st.write(
                        "**Hospital:**",
                        result["hospital"]
                    )

                    st.write(
                        "**Assigned Bed:**",
                        result["hospital_bed"]
                    )

                    st.write(
                        "**Hospital Route:**",
                        " → ".join(result["hospital_route"])
                    )

                    st.metric(
                        "Total Journey Distance",
                        f"{result['total_distance']:.2f} km"
                    )

                    st.rerun()

                else:
                    st.error(result["message"])

        else:
            st.success("No pending emergencies.")

    else:
        st.info("No patients registered.")

    st.divider()

    st.subheader("Recent Allocations")

    if not allocations.empty:

        st.dataframe(
            allocations.sort_values(
                "id",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No allocations have been performed yet.")


# ==================================================
# REPORTS AND HISTORY
# ==================================================

elif page == "Reports & History":

    st.title("📊 Reports & History")

    st.caption(
        "Review historical emergency and dispatch records."
    )

    st.subheader("Emergency Records")

    if not patients.empty:

        st.dataframe(
            patients.sort_values(
                "id",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No emergency records available.")

    st.divider()

    st.subheader("Dispatch History")

    if not dispatches.empty:

        st.dataframe(
            dispatches.sort_values(
                "id",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No dispatch history available.")

    st.divider()

    st.subheader("Allocation History")

    if not allocations.empty:

        st.dataframe(
            allocations.sort_values(
                "id",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No allocation history available.")
