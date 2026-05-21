import pandas as pd

file_path = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\proyecto_EDGE.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    df_wbs = xl.parse("WBS_OUTPUT (No editar)")
    print("Columns:", list(df_wbs.columns))
    
    df_clas = xl.parse("Clasificacion EDGE")
    print("\n--- Clasificacion EDGE ---")
    print(df_clas.head(5).to_string())
    
except Exception as e:
    print("Error reading Excel:", e)
