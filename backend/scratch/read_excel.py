import pandas as pd
import sys

file_path = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\docs\Documentos_EOSIS\WBS_Certificacion_EDGE_Outputs para Smartsuite.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print("Sheets available:", xl.sheet_names)
    
    for sheet in xl.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        df = xl.parse(sheet)
        print("Columns:", list(df.columns))
        print("First 3 rows:")
        print(df.head(3).to_string())
except Exception as e:
    print("Error reading Excel:", e)
