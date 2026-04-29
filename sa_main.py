import streamlit as st
import pandas as pd
from data_loader import get_all_courses
from sa_engine import SAScheduler

# Constants
ROOMS = [f"Room {i}" for i in range(1, 51)]
COMPUTING_LABS = [f"Comp-Lab {i}" for i in range(1, 11)]
DIGITAL_LAB = ["B-Digital"]
ENGLISH_LABS = [f"English-Lab {i}" for i in range(1, 6)]
ALL_LABS = COMPUTING_LABS + DIGITAL_LAB + ENGLISH_LABS

st.set_page_config(page_title="IntelliSched SA", layout="wide")
st.title("🔥 Simulated Annealing Timetable Generator")

if st.sidebar.button("Load Data"):
    paths = {"Theory": "Computing-Theory.csv", "Labs": "Computing-Labs.csv", "MG": "MG.csv", "S&H": "S&H.csv"}
    st.session_state['courses'] = get_all_courses(paths)
    st.sidebar.success("Data Loaded!")

if 'courses' in st.session_state:
    # SA Specific Inputs
    st.sidebar.subheader("SA Hyperparameters")
    init_temp = st.sidebar.number_input("Initial Temperature", value=100.0)
    cooling = st.sidebar.slider("Cooling Rate", 0.80, 0.99, 0.95)
    iters = st.sidebar.number_input("Max Iterations", value=2000)

    if st.sidebar.button("Generate SA Schedule"):
        scheduler = SAScheduler(st.session_state['courses'], ROOMS, COMPUTING_LABS, DIGITAL_LAB, ENGLISH_LABS, init_temp, cooling)
        best_sol, final_conflicts = scheduler.solve(iterations=iters)
        
        st.sidebar.info(f"Final Conflict Count: {final_conflicts}")
        
        theory_times = ["08:30-09:50", "10:00-11:20", "11:30-12:50", "01:00-02:20", "02:30-03:50", "04:00-05:15"]
        lab_times = ["08:30-11:15", "11:30-02:15", "02:30-05:15"]
        
        day_tabs = st.tabs(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
            with day_tabs[i]:
                theory_grid = pd.DataFrame("-", index=ROOMS, columns=theory_times)
                lab_grid = pd.DataFrame("-", index=ALL_LABS, columns=lab_times)
                
                for item in best_sol:
                    if item['day'] == day:
                        content = f"{item['course'].name}\n({item['course'].section})"
                        if item['is_lab']: lab_grid.at[item['room'], item['slot']] = content
                        else: theory_grid.at[item['room'], item['slot']] = content
                
                st.subheader(f"🏛️ {day}: Theory")
                st.dataframe(theory_grid, use_container_width=True)
                st.subheader(f"🧪 {day}: Labs")
                st.dataframe(lab_grid, use_container_width=True)