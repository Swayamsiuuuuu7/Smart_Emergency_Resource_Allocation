
# Aim: To register emergency cases and store patient details in SQLite.

import streamlit as st
import sqlite3
from datetime import datetime

print("Swayam Arora - 1/24/SET/BCS/349")

DB_NAME = "emergency.db"

st.set_page_config(
    page_title="New Emergency Dispatch",
    page_icon="🚨",
    layout="wide"
)

# DATABASE CONNECTION
def connect_db():
    return sqlite3.connect(DB_NAME)

# DATABASE MIGRATION
def initialize_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(patients)")
    columns = [row[1] for row in cur.fetchall()]

    if "phone" not in columns:
        cur.execute("ALTER TABLE patients ADD COLUMN phone TEXT")

    if "created_at" not in columns:
        cur.execute("ALTER TABLE patients ADD COLUMN created_at TIMESTAMP")

    conn.commit()
    conn.close()

initialize_database()

# PAGE DESIGN
st.markdown("""
<style>
.stApp {
    background: #F4F7FB;
}
[data-testid="stSidebar"] {
    background: white;
}
.block-container {
    padding-top: 2rem;
}
.emergency-header {
    background: #FFFFFF;
    padding: 24px;
    border-radius: 14px;
    border: 1px solid #E2E8F0;
    margin-bottom: 20px;
}
.emergency-header h2 {
    color: #243247;
}
.emergency-header p {
    color: #64748B;
}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="emergency-header">
    <h2>🚨 New Emergency Registration</h2>
    <p>Register a new emergency case and initiate the dispatch workflow.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    ""
)

# EMERGENCY FORM
st.subheader("Patient Information")

with st.form("emergency_registration", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:
        patient_name = st.text_input(
            "Patient Full Name *",
            placeholder="Enter patient name"
        )

        phone = st.text_input(
            "Contact Number",
            placeholder="Enter contact number"
        )

        emergency_type = st.selectbox(
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
            ["Critical", "High", "Moderate", "Low"]
        )

        location = st.selectbox(
            "Patient Location",
            ["Central", "North", "South", "East", "West"]
        )

        additional_details = st.text_area(
            "Additional Information",
            placeholder="Enter relevant emergency details..."
        )

    st.divider()

    st.subheader("Emergency Priority")

    priority_values = {
        "Critical": 4,
        "High": 3,
        "Moderate": 2,
        "Low": 1
    }

    priority = priority_values[severity]

    p1, p2 = st.columns(2)

    p1.metric("Priority Score", priority)
    p2.metric("Emergency Level", severity)

    submitted = st.form_submit_button(
        "REGISTER EMERGENCY",
        type="primary",
        use_container_width=True
    )

    if submitted:

        if not patient_name.strip():
            st.error("Please enter the patient's name.")

        elif phone and not phone.isdigit():
            st.error("Contact number should contain digits only.")

        else:
            conn = connect_db()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO patients
                (name, emergency, severity, location, status, phone)
                VALUES (?, ?, ?, ?, 'Pending', ?)
            """, (
                patient_name.strip(),
                emergency_type,
                severity,
                location,
                phone
            ))

            patient_id = cur.lastrowid

            conn.commit()
            conn.close()

            st.session_state["new_patient_id"] = patient_id
            st.session_state["new_patient_name"] = patient_name.strip()

            st.success(
                f"Emergency registered successfully! Patient ID: {patient_id}"
            )

            st.info(
                "The emergency is now registered and waiting for resource allocation."
            )

# RECENT EMERGENCIES
st.divider()
st.subheader("Recently Registered Emergencies")

conn = connect_db()

import pandas as pd

recent = pd.read_sql_query("""
    SELECT id, name, phone, emergency, severity, location, status
    FROM patients
    ORDER BY id DESC
    LIMIT 10
""", conn)

conn.close()

if not recent.empty:
    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No emergency cases registered yet.")

