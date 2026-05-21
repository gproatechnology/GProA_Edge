import pandas as pd
import os

docs_dir = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\docs\Documentos_EOSIS"
files = [
    "EEM01_WWR_Tristone.xlsx",
    "Tristone_Area Breakdown_Calculator.xlsx"
]

for f in files:
    path = os.path.join(docs_dir, f)
    if os.path.exists(path):
        try:
            xl = pd.ExcelFile(path)
            print(f"--- Archivo: {f} ---")
            print("Pestañas:", xl.sheet_names)
            
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                print(f"  Hoja '{sheet}': {len(df)} filas, {len(df.columns)} columnas")
                
        except Exception as e:
            print(f"Error reading {f}: {e}")
    else:
        print(f"File not found: {path}")
