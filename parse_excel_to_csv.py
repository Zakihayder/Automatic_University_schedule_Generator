import pandas as pd
import os
import numpy as np
def convert_excel_to_clean_csv(excel_path):
    """
    Reads the university Excel file, cleans merged cells, 
    and saves each relevant sheet as a separate CSV.
    """
    if not os.path.exists(excel_path):
        print(f"Error: Could not find the file '{excel_path}'. Please make sure it is in the same folder.")
        return

    # Load the Excel file
    print("Reading Excel file...")
    xl = pd.ExcelFile(excel_path)
    
    # Mapping of Sheet Names to the Category they represent
    # Update these keys if your sheet names are slightly different
    sheet_map = {
        'Computing-Theory': 'Computing-Theory.csv',
        'Computing-Labs': 'Computing-Labs.csv',
        'MG': 'MG.csv',
        'S&H': 'S&H.csv'
    }

    for sheet, output_name in sheet_map.items():
        if sheet in xl.sheet_names:
            # We skip the first few rows because university files usually have headers/titles
            # header=2 usually starts at S.#, Code, Course, etc.
            df = pd.read_excel(excel_path, sheet_name=sheet, header=2)
            
            # CLEANING STEP: Handle Merged Cells
            # If 'Code' or 'CHs' is empty, it takes the value from the row above
            if 'Code' in df.columns:
                df['Code'] = df['Code'].ffill()
            if 'CHs' in df.columns:
                df['CHs'] = df['CHs'].ffill()
            if 'Course' in df.columns:
                df['Course'] = df['Course'].ffill()

            # Save to CSV
            df.to_csv(output_name, index=False)
            print(f"✅ Created: {output_name}")
        else:
            print(f"⚠️ Warning: Sheet '{sheet}' not found in Excel file.")

if __name__ == "__main__":
    # CHANGE THIS to your actual filename
    MY_FILE = "Tentative list of Courses, FSC, FAST-NUCES, Islamabad, Spring-2026.xlsx"
    convert_excel_to_clean_csv(MY_FILE)
