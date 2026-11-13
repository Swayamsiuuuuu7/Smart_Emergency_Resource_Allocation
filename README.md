# 🚑 Smart Emergency Resource Allocation System

A Python-based emergency management system that intelligently allocates ambulances and hospital beds to emergency patients using **Priority Queue, Dijkstra's Shortest Path Algorithm, and Greedy Approach**.

## 📌 Project Overview

The Smart Emergency Resource Allocation System is designed to improve emergency response by prioritizing patients based on their severity and allocating the nearest available ambulance and hospital bed.

The system calculates routes and distances to support efficient resource allocation and provides a centralized dashboard for monitoring emergency operations.

## 🎯 Objectives

- Prioritize emergency cases according to severity.
- Allocate the nearest available ambulance.
- Find efficient routes using Dijkstra's Algorithm.
- Assign available hospital beds.
- Reduce unnecessary delays in emergency resource allocation.
- Maintain patient records and dispatch history.

## ⚙️ Technologies Used

- **Programming Language:** Python
- **Frontend:** Streamlit
- **Database:** SQLite
- **Data Handling:** Pandas
- **Visualization:** Plotly
- **Algorithms:** Priority Queue, Dijkstra's Algorithm, Greedy Approach

## 🧠 Algorithms Implemented

### 1. Priority Queue
Prioritizes patients based on emergency severity so that critical cases receive attention before lower-priority cases.

### 2. Dijkstra's Shortest Path Algorithm
Calculates the shortest route between locations using the available road network and associated distances.

### 3. Greedy Approach
Selects nearby available resources, such as ambulances and hospital beds, to support efficient allocation.

## ✨ Key Features

- **Emergency Registration:** Register patients with emergency type, severity, location, and contact details.
- **Patient Management:** View and manage registered emergency records.
- **Ambulance Management:** Monitor ambulance availability and locations.
- **Hospital Management:** Track available and occupied hospital beds.
- **Smart Allocation:** Allocate emergency resources using the implemented algorithms.
- **Route Calculation:** Display ambulance pickup and hospital routes with distances.
- **Dashboard:** View emergency statistics and resource utilization.
- **Reports & History:** Access previous allocations and dispatch records.

## 📍 System Locations

The system currently uses five emergency pickup locations:

- A Block
- B Block
- C Block
- G Block
- T Block

All emergency patients are transported to **Central Hospital** in the current simulation.

## 📂 Project Structure

```text
Smart_Emergency_Resource_Allocation/
│
├── app.py
│
├── core/
│   ├── algorithms.py
│   └── allocation.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Smart_Emergency_Resource_Allocation.git
```

### 2. Navigate to the Project Directory

```bash
cd Smart_Emergency_Resource_Allocation
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python3 -m streamlit run app.py
```

The application will open in your browser.

## 🖥️ Application Modules

1. Overview Dashboard
2. Patient Management
3. Ambulance Management
4. Hospital Management
5. Smart Allocation
6. Reports & History
7. New Emergency Registration

## 📊 Expected System Workflow

1. Register a new emergency patient.
2. Assign an emergency severity level.
3. Prioritize the patient using the priority mechanism.
4. Identify the nearest available ambulance.
5. Calculate the shortest route using Dijkstra's Algorithm.
6. Allocate an available hospital bed.
7. Update resource availability and save dispatch records.

## 🔮 Future Scope

- Integration with real-time GPS tracking.
- Live traffic-based route optimization.
- Integration with real hospital databases.
- Multiple hospital support.
- Real-time ambulance monitoring.
- Mobile application integration.

## 👨‍💻 Project Information

**Project Title:** Smart Emergency Resource Allocation System

**Domain:** Design and Analysis of Algorithms (DAA)

**Developed By:**
- Swayam Arora
- Ishu
- Karishma

## ⚠️ Disclaimer

This project is developed for academic and educational purposes. It is a simulation of emergency resource allocation and is not intended to replace real-world emergency response services.

---

**Smart Emergency Resource Allocation System**  
*Making Emergency Resource Allocation Smarter and More Efficient.*
