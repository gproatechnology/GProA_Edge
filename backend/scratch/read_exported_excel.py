import pandas as pd
import sys

file_path = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\proyecto_EDGE.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print("Sheets in generated Excel:", xl.sheet_names)
    
    if "WBS_OUTPUT (No editar)" in xl.sheet_names:
        df_wbs = xl.parse("WBS_OUTPUT (No editar)")
        # Look for the EEM22 row to see if hours were zeroed out
        print("\n--- Checking WBS_OUTPUT for EEM22 ---")
        mask = df_wbs['Actividad'].astype(str).str.contains('EEM22')
        if mask.any():
            row = df_wbs[mask]
            print(row[['Actividad', 'HPen CS', 'HPen PM']].to_string())
        else:
            print("No EEM22 activity found.")
            
    if "Clasificacion EDGE" in xl.sheet_names:
        print("\n--- Clasificacion EDGE ---")
        df_clas = xl.parse("Clasificacion EDGE")
        print(f"Total rows: {len(df_clas)}")
        print(df_clas.head(3).to_string())
        
except Exception as e:
    print("Error reading Excel:", e)
