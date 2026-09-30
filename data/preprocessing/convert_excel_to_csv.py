import pandas as pd
from pathlib import Path

def convert_excel_to_csv(excel_path):
    # Ensure the file exists
    if not Path(excel_path).exists():
        print(f"Error: Could not find the file at {excel_path}")
        return

    print(f"Loading Excel file: {excel_path}...")
    
    # 1. Load the entire Excel file using openpyxl engine
    excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
    
    # 2. Iterate through all sheet names
    for sheet_name in excel_file.sheet_names:
        print(f"Processing sheet: '{sheet_name}'...")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # 3. Construct output filename based on sheet name
        output_filename = f"data/raw/{Path(excel_path).stem}_{sheet_name}.csv"
        
        # 4. Save to CSV using utf-8-sig to preserve Polish symbols
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"Successfully saved {sheet_name} to {output_filename}")

if __name__ == "__main__":
    excel_path = "data/raw/lokaty.xlsx"
    convert_excel_to_csv(excel_path)
