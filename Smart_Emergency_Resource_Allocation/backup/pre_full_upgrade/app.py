
# Aim: To develop an advanced Smart Emergency Resource Allocation System.

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

print("Swayam Arora - 1/24/SET/BCS/349")

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

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

# --------------------------------------------------
# CUSTOM LIGHT THEME
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FB;
    color: #243247;
}

[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E5EAF2;
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

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def connect_db():
    return sqlite3.connect(DB_NAME)


def initialize_database():

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        PRAGMA table_info(patients)
    """)

    columns = [
        row[1] for row in cur.fetchall()
    ]

    if "phone" not in columns:
        cur.execute("""
            ALTER TABLE patients ADD COLUMN phone TEXT
        """)

    if "details" not in columns:
        cur.execute("""
            ALTER TABLE patients ADD COLUMN details TEXT
        """)

    conn.commit()
    conn.close()


def get_data(query):

    try:
        conn = connect_db()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    except Exception:
        return pd.DataFrame()


initialize_database()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

if "active_page" not in st.session_state:
    st.session_state.active_page = "Overview"


def set_page(selected_page):
    st.session_state.active_page = selected_page


with st.sidebar:

    st.markdown("## 🚑 ER COMMAND")
    st.caption("Emergency Response System")

    st.divider()

    # SINGLE NEW EMERGENCY BUTTON

    st.button(
        "🚨 NEW EMERGENCY",
        type="primary",
        use_container_width=True,
        on_click=set_page,
        args=("New Emergency",)
    )

    st.divider()

    st.markdown("### MAIN MENU")

    navigation = [
        "Overview",
        "Patient Management",
        "Ambulance Management",
        "Hospital Management",
        "Emergency Map",
        "Smart Allocation",
        "Algorithm Laboratory",
        "Simulation Center",
        "Reports & History"
    ]

    for item in navigation:

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

    st.caption("Educational Simulation")
    st.caption("DAA Project | 2026")


page = st.session_state.active_page


# --------------------------------------------------
# DATABASE STATISTICS
# --------------------------------------------------

patients = get_data(
    "SELECT * FROM patients"
)

resources = get_data(
    "SELECT * FROM resources"
)

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

    total_patients = 0
    pending = 0
    allocated = 0
    critical = 0


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

    available_ambulances = 0
    available_beds = 0
    total_ambulances = 0
    total_beds = 0


# --------------------------------------------------
# NEW EMERGENCY SCREEN
# --------------------------------------------------

if page == "New Emergency":

    st.title("🚨 Emergency Dispatch Center")

    st.caption(
        "Register a patient and initiate an emergency response."
    )

    st.warning(
        "Educational simulation only. "
        "This application is not a real emergency dispatch service."
    )

    st.subheader("Patient Information")

    with st.form(
        "quick_emergency",
        clear_on_submit=True
    ):

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
            "🚨 REGISTER EMERGENCY",
            type="primary",
            use_container_width=True
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Please enter the patient's name."
                )

            elif phone and not phone.isdigit():

                st.error(
                    "Contact number must contain digits only."
                )

            else:

                conn = connect_db()
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
                conn.close()

                st.success(
                    f"Emergency registered successfully! "
                    f"Patient ID: {patient_id}"
                )

                st.info(
                    "The patient has been added to the "
                    "emergency queue and is awaiting allocation."
                )


# --------------------------------------------------
# OVERVIEW DASHBOARD
# --------------------------------------------------

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
        (
            c1,
            "Total Emergencies",
            total_patients,
            "All registered cases"
        ),
        (
            c2,
            "Critical Patients",
            critical,
            "Require urgent attention"
        ),
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

        st.markdown(
            "### Emergency Severity Distribution"
        )

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
                margin=dict(
                    t=20,
                    b=20,
                    l=20,
                    r=20
                ),
                legend_title_text=""
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "No emergency records available yet."
            )

    with right:

        st.markdown("### Patient Status")

        status_data = pd.DataFrame({
            "Status": [
                "Pending",
                "Allocated"
            ],
            "Patients": [
                pending,
                allocated
            ]
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
            margin=dict(
                t=20,
                b=20,
                l=20,
                r=20
            ),
            yaxis_title="Number of Patients"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # RESOURCE UTILIZATION

    st.subheader("Resource Utilization")

    r1, r2 = st.columns(2)

    with r1:

        st.markdown("**Ambulance Fleet**")

        ambulance_usage = (
            (
                total_ambulances -
                available_ambulances
            ) / total_ambulances * 100
            if total_ambulances else 0
        )

        st.progress(
            int(ambulance_usage)
        )

        st.write(
            f"{ambulance_usage:.1f}% currently allocated"
        )

    with r2:

        st.markdown("**Hospital Beds**")

        bed_usage = (
            (
                total_beds -
                available_beds
            ) / total_beds * 100
            if total_beds else 0
        )

        st.progress(
            int(bed_usage)
        )

        st.write(
            f"{bed_usage:.1f}% currently occupied"
        )

    st.divider()

    # RECENT EMERGENCY ACTIVITY

    st.subheader("Recent Emergency Activity")

    if not patients.empty:

        recent = (
            patients
            .sort_values("id", ascending=False)
            .head(8)
        )

        display_columns = [
            "id",
            "name",
            "emergency",
            "severity",
            "location",
            "status"
        ]

        st.dataframe(
            recent[display_columns],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No emergency activity recorded."
        )


# --------------------------------------------------
# OTHER MODULES
# --------------------------------------------------

else:

    st.title(page)

    st.info(
        f"The {page} module will be implemented "
        "in the upcoming development phases."
    )

    st.caption(
        "All modules will be connected to the same SQLite database."
    )
