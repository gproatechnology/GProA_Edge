import pandas as pd
file_path = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\docs\Documentos_EOSIS\WBS_Certificacion_EDGE_Outputs para Smartsuite.xlsx"
df = pd.read_excel(file_path, sheet_name="WBS_OUTPUT (No editar)")
print(df[['Bloque', 'Actividad']].dropna().to_string())
