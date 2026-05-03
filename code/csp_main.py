# Importing Libraries
import streamlit as st
import pandas as pd
from data_loader import get_all_courses
from csp_engine import CSPScheduler

# Infrastructure remains consistent with your original main.py
ROOMS = [f"Room {i}" for i in range(1, 51)]
COMPUTING_LABS = [f"Comp-Lab {i}" for i in range(1, 11)]
DIGITAL_LAB = ["B-Digital"]
ENGLISH_LABS = [f"English-Lab {i}" for i in range(1, 6)]
ALL_LABS = COMPUTING_LABS + DIGITAL_LAB + ENGLISH_LABS

st.set_page_config(page_title="IntelliSched CSP", layout="wide")
st.title("🧩 CSP University Timetable Generator")

if st.sidebar.button("Load Data"):
    paths = {"Theory": "data/Computing-Theory.csv", "Labs": "data/Computing-Labs.csv", "MG": "data/MG.csv", "S&H": "data/S&H.csv"}
    st.session_state['courses'] = get_all_courses(paths)
    st.sidebar.success("Data Loaded!")

if 'courses' in st.session_state:
    st.info("Note: CSP uses Backtracking Search. Large datasets may take longer due to combinatorial complexity.")
    
    if st.sidebar.button("Generate CSP Schedule"):
        scheduler = CSPScheduler(st.session_state['courses'], ROOMS, COMPUTING_LABS, DIGITAL_LAB, ENGLISH_LABS)
        solution = scheduler.solve()
        
        if solution:
            st.sidebar.success("Valid CSP Solution Found!")
            # Use the same formatting logic as your main.py to display the grids
            theory_times = ["08:30-09:50", "10:00-11:20", "11:30-12:50", "01:00-02:20", "02:30-03:50", "04:00-05:15"]
            lab_times = ["08:30-11:15", "11:30-02:15", "02:30-05:15"]
            
            day_tabs = st.tabs(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
                with day_tabs[i]:
                    theory_grid = pd.DataFrame("-", index=ROOMS, columns=theory_times)
                    lab_grid = pd.DataFrame("-", index=ALL_LABS, columns=lab_times)
                    
                    for item in solution:
                        if item['day'] == day:
                            content = f"{item['course'].name}\n({item['course'].section})"
                            if item['is_lab']: lab_grid.at[item['room'], item['slot']] = content
                            else: theory_grid.at[item['room'], item['slot']] = content
                    
                    st.subheader(f"🏛️ {day}: Theory")
                    st.dataframe(theory_grid, use_container_width=True)
                    st.subheader(f"🧪 {day}: Labs")
                    st.dataframe(lab_grid, use_container_width=True)
        else:
            st.error("No valid solution found within constraints (Unsatisfiable).")