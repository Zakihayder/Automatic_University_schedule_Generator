import streamlit as st
import pandas as pd
from data_loader import get_all_courses
from engine import GeneticScheduler

# 1. INFRASTRUCTURE
ROOMS = [f"Room {i}" for i in range(1, 51)]
COMPUTING_LABS = [f"Comp-Lab {i}" for i in range(1, 11)]
DIGITAL_LAB = ["B-Digital"]
ENGLISH_LABS = [f"English-Lab {i}" for i in range(1, 6)]
ALL_LABS = COMPUTING_LABS + DIGITAL_LAB + ENGLISH_LABS

# 2. CSS FOR TEXT WRAPPING & STYLING
st.markdown("""
    <style>
    /* Target all cells in the dataframe */
    .stDataFrame div[data-testid="stTable"] td, 
    .stDataFrame div[data-testid="stTable"] th {
        white-space: normal !important;
        word-wrap: break-word !important;
        text-align: center !important;
        vertical-align: middle !important;
        padding: 10px !important;
        line-height: 1.4 !important;
    }
    /* Increase column width to ensure 3-4 words fit per line */
    [data-testid="stDataFrame"] {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

def get_batch_color(val):
    if not val or val == "-": return ""
    val = str(val).upper()
    if "BCS" in val: return "background-color: #D1E8FF; color: black;"
    if "BSE" in val: return "background-color: #D1FFD7; color: black;"
    if "BAI" in val: return "background-color: #FFE4D1; color: black;"
    if "BDS" in val: return "background-color: #F3D1FF; color: black;"
    if "BCY" in val: return "background-color: #FFD1D1; color: black;"
    return "background-color: #F0F2F6; color: black;"

st.set_page_config(page_title="IntelliSched AI", layout="wide")
st.title("🎓 Automatic University Timetable Generator")

# 3. DATA LOADING (Sidebar)
if st.sidebar.button("Load Data"):
    paths = {"Theory": "Computing-Theory.csv", "Labs": "Computing-Labs.csv", "MG": "MG.csv", "S&H": "S&H.csv"}
    st.session_state['courses'] = get_all_courses(paths)
    st.sidebar.success("Data Loaded!")

# 4. GRID GENERATION
if 'courses' in st.session_state:
    generations = st.sidebar.slider("GA Generations", 10, 200, 100)
    
    if st.sidebar.button("Generate Time-Table"):
        scheduler = GeneticScheduler(st.session_state['courses'], ROOMS, COMPUTING_LABS, DIGITAL_LAB, ENGLISH_LABS)
        best_schedule = scheduler.evolve(generations=generations)
        
        theory_times = ["08:30-09:50", "10:00-11:20", "11:30-12:50", "01:00-02:20", "02:30-03:50", "04:00-05:15"]
        lab_times = ["08:30-11:15", "11:30-02:15", "02:30-05:15"]
        
        tabs = st.tabs(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
            with tabs[i]:
                # --- SECTION 1: THEORY ROOMS ---
                st.markdown(f"### 🏛️ {day}: Theory Classes")
                theory_grid = pd.DataFrame("-", index=ROOMS, columns=theory_times)
                
                # --- SECTION 2: SPECIALIZED LABS ---
                lab_grid = pd.DataFrame("-", index=ALL_LABS, columns=lab_times)
                
                # Fill grids
                for item in best_schedule:
                    if item['day'] == day:
                        # Content formatted with newlines for better vertical display
                        content = f"{item['course'].name}\n{item['course'].code}\n({item['course'].section})"
                        
                        if item['is_lab']:
                            if item['room'] in lab_grid.index:
                                lab_grid.at[item['room'], item['slot']] = content
                        else:
                            if item['room'] in theory_grid.index:
                                theory_grid.at[item['room'], item['slot']] = content

                # Helper function to apply centering and batch colors
                def apply_final_style(styler):
                    styler.applymap(get_batch_color)
                    # This ensures the text inside the styled dataframe is centered
                    styler.set_properties(**{
                        'text-align': 'center',
                        'white-space': 'normal',
                        'height': 'auto'
                    })
                    return styler

                # Display Tables
                st.dataframe(apply_final_style(theory_grid.style), use_container_width=True, height=600)
                
                st.divider()
                
                st.markdown(f"### 🧪 {day}: Lab Sessions")
                st.dataframe(apply_final_style(lab_grid.style), use_container_width=True, height=400)