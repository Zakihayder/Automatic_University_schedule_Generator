# 🎓 IntelliSched: AI-Driven University Timetable Generator

**IntelliSched** is an automated scheduling system developed for the FAST School of Computing (NUCES, Islamabad) for the Spring-2026 semester. It utilizes a **Genetic Algorithm (Local Search)** to solve the complex, NP-Hard problem of university course scheduling.

---

## 🚀 Key Features
* **Smart Constraint Satisfaction:** Avoids instructor, room, and section overlaps.
* **Domain-Specific Lab Logic:** Distinguishes Computing Labs, English Labs, and the B-Digital Lab.
* **Hybrid Time-Slot Management:** Handles overlapping 80-minute theory slots and 165-minute lab slots.
* **Strict Credit-Hour Integrity:** 1-CH labs and 2-CH theory appear once per week; 3-CH theory appears twice.
* **Real-Time Availability Spotlight:** Find free rooms by day/slot with capacity filtering.
* **Smart-Booker:** Validates mutual free slots for a teacher and section.
* **Student Path View:** Shows a single course timetable per section.
* **Substitution Finder:** Suggests free, qualified instructors.
* **Utilization Analytics:** Peak hours and under-utilized rooms.

---

## 🧠 AI Strategy: Genetic Algorithm (Part B)

The core of this project is a **Search-Based Optimization** algorithm that mimics biological evolution to "evolve" a conflict-free schedule.

### 1. Representation (State Space)
Each **Chromosome** (Schedule) consists of a list of **Genes** (Assignments). 
* **Gene Structure:** `(Course, Instructor, Section, Room, Day, Time Slot)`

### 2. Heuristic Function (Fitness)
The algorithm uses an **Informed Search** guided by a Fitness Function. The goal is to maximize fitness (minimize conflicts).

Fitness = 1/(1 + H_c)

**Hard Conflicts (H_c) include:**
* **Instructor Conflict:** A teacher assigned to two different rooms at the same time.
* **Room Conflict:** Two different courses assigned to the same room at the same time.
* **Section Conflict:** A student batch (e.g., BSE-2B) having two different classes at the same time.

**Soft Penalties (S_c) include:**
* **Room Persistence:** Prefer same room for consecutive classes.
* **Teacher Preference:** Honor preferred slots when provided.
* **Load Balancing:** Avoid more than 3 consecutive classes.



### 3. Evolutionary Operators
* **Selection:** Uses **Elitism** to carry the top 10% of the best-performing schedules into the next generation.
* **Crossover:** Combines "good" parts of two different schedules to create superior offspring.
* **Smart Mutation:** To escape local optima, the AI randomly relocates a class to a new room or time slot while respecting the **Lab vs. Theory** facility constraints.

---

## 🏛️ Infrastructure Constraints
The AI manages the following physical resources:
* **50 Theory Rooms:** For standard 3-Credit and 2-Credit courses.
* **10 Computing Labs:** Dedicated to programming courses (PF, OOP, DB, OS, etc.).
* **5 English/S&H Labs:** For communication and humanities-related courses.
* **1 B-Digital Lab:** Exclusively reserved for DLD and Digital Logic sessions.

---

## 📁 Project Structure
```
code/           # Application source code
data/           # CSV inputs and Excel source data
data/images/    # UI assets (Logo.jpg)
```

---


## 🛠️ Execution Instructions & Dependencies

### 1. System Requirements
* **Python Version:** 3.8 or higher.
* **OS:** Windows, macOS, or Linux.

### 2. Dependencies
Install the required libraries using the following command:
```bash
pip install streamlit pandas openpyxl

```
## Step-by-Step Execution
Prepare Data: Place your Excel file in the data folder.

## Data Cleaning: Run the preprocessing script to clean merged cells and generate theory/lab CSVs:

```bash
python code/parse_excel_to_csv.py
```

Launch Interface: Run the Streamlit application:

```bash
streamlit run code/main.py
```

Generate: Click "Load Data," adjust the "GA Generations" slider, and press "Generate Time-Table"

---

## 🧪 UI Modules
* **By Day:** Single-day room/lab grid.
* **By Section:** Section-focused timetable.
* **Performance:** Validation report, accuracy, and fitness curve.
* **Availability:** Room free/busy spotlight with capacity filter.
* **Smart-Booker:** Mutual free slots between teacher and section.
* **Student Path:** Course timetable lookup.
* **Substitution:** Substitute instructor suggestions.
* **Analytics:** Room utilization and peak hours.

---

## ⚙️ Notes and Tips
* If a teacher is missing in CSV, a placeholder instructor is assigned so the class still schedules.
* Results can vary by run; increase **Population Size** and **Restart Attempts** for higher quality.
* If you change CSV column names, update the loader in `code/data_loader.py`.