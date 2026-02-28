import pandas as pd
from models import CourseSection

def process_sheet(file_path, sheet_name, category):
    """
    Cleans a specific sheet from the university file.
    Follows your instruction: Ignore Coordinator, focus on Code, CH, Section, Instructor.
    """
    try:
        # Load the CSV/Excel sheet (Assuming CSV for this script)
        df = pd.read_csv(file_path)
        
        # Standardizing column names based on your sheet description
        # We handle cases where 'Course Instructor' might have empty rows (forward fill)
        df['Code'] = df['Code'].ffill()
        df['CHs'] = df['CHs'].ffill()
        
        course_list = []
        
        for _, row in df.iterrows():
            # Skip rows where instructor is missing or placeholder
            if pd.isna(row['Course Instructor']) or str(row['Course Instructor']).strip() == "":
                continue
            
            section_obj = CourseSection(
                code=row['Code'],
                name=row.get('Course', 'N/A'),
                ch=row['CHs'],
                section=row['Section'],
                instructor=row['Course Instructor'],
                category=category
            )
            course_list.append(section_obj)
            
        return course_list
    except Exception as e:
        print(f"Error processing {category}: {e}")
        return []

def get_all_courses(file_map):
    """
    file_map: Dictionary where keys are categories and values are file paths.
    """
    all_scheduled_items = []
    for category, path in file_map.items():
        all_scheduled_items.extend(process_sheet(path, None, category))
    
    return all_scheduled_items

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    # Update these paths to your local file names
    paths = {
        "Theory": "Computing-Theory.csv",
        "Labs": "Computing-Labs.csv",
        "MG": "MG.csv",
        "S&H": "S&H.csv"
    }
    
    full_course_load = get_all_courses(paths)
    print(f"Successfully loaded {len(full_course_load)} course sections for scheduling.")
    
    # Example check
    if full_course_load:
        print(f"First item: {full_course_load[0]}")
        print(f"Sessions for 3CH: {full_course_load[0].sessions_per_week}")