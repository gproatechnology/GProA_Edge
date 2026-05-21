import pandas as pd
import sys

file_path = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\docs\Documentos_EOSIS\proyecto_EDGE.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print("Pestañas en el Excel generado:", xl.sheet_names)
    
    # Check WBS output for zeroed hours
    if "WBS_OUTPUT (No editar)" in xl.sheet_names:
        df_wbs = xl.parse("WBS_OUTPUT (No editar)")
        # Look for the EEM22 row to see if hours were zeroed out
        print("\n--- Checking WBS_OUTPUT for Completed Measures ---")
        # Find rows where HPen CS is 0
        if 'HPen CS' in df_wbs.columns:
            completed_mask = df_wbs['HPen CS'] == 0
            if completed_mask.any():
                print("Actividades completadas (horas en 0):")
                print(df_wbs[completed_mask][['Actividad', 'HPen CS']].to_string())
            else:
                print("No se encontraron actividades con horas reducidas a 0.")
        else:
            print("No se encontró la columna HPen CS")
            
    # Check Classification
    if "Clasificacion EDGE" in xl.sheet_names:
        print("\n--- Clasificacion EDGE ---")
        df_clas = xl.parse("Clasificacion EDGE")
        print(f"Archivos procesados: {len(df_clas)}")
        print(df_clas[['Archivo', 'Categoria', 'Medida', 'Estado']].head().to_string())

    # Check Luminarias
    if "EEM22 Luminarias" in xl.sheet_names:
        print("\n--- EEM22 Luminarias ---")
        df_lum = xl.parse("EEM22 Luminarias")
        print(f"Total registros: {len(df_lum)}")
        print(df_lum.head(5).to_string())

    # Check Areas
    if "Areas" in xl.sheet_names:
        print("\n--- Areas Extraidas ---")
        df_areas = xl.parse("Areas")
        print(f"Total registros: {len(df_areas)}")
        print(df_areas.head(5).to_string())
        
except Exception as e:
    print("Error reading Excel:", e)
