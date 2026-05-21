import os
import win32com.client as win32

# Use absolute paths for win32com
base_dir = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge"
wbs_path = os.path.join(base_dir, r"backend\app\assets\wbs_template.xlsx")
wwr_path = os.path.join(base_dir, r"docs\Documentos_EOSIS\EEM01_WWR_Tristone.xlsx")
areas_path = os.path.join(base_dir, r"docs\Documentos_EOSIS\Tristone_Area Breakdown_Calculator.xlsx")

excel = None
try:
    print("Iniciando Excel en segundo plano...")
    excel = win32.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    
    print("Abriendo WBS Template...")
    wb_master = excel.Workbooks.Open(wbs_path)
    
    # 1. WWR
    print("Abriendo WWR Calculator...")
    wb_wwr = excel.Workbooks.Open(wwr_path)
    sheet_wwr = wb_wwr.Worksheets("Hoja 3")
    # Copiar antes de la primera hoja del master (o despues de la ultima)
    sheet_wwr.Copy(After=wb_master.Worksheets(wb_master.Worksheets.Count))
    new_sheet_wwr = wb_master.Worksheets(wb_master.Worksheets.Count)
    new_sheet_wwr.Name = "Calculadora WWR"
    wb_wwr.Close(False)
    print("WWR copiado exitosamente.")
    
    # 2. Areas
    print("Abriendo Area Breakdown...")
    wb_areas = excel.Workbooks.Open(areas_path)
    sheet_areas = wb_areas.Worksheets("Hoja 1")
    sheet_areas.Copy(After=wb_master.Worksheets(wb_master.Worksheets.Count))
    new_sheet_areas = wb_master.Worksheets(wb_master.Worksheets.Count)
    new_sheet_areas.Name = "Calculadora Areas"
    wb_areas.Close(False)
    print("Areas copiado exitosamente.")
    
    wb_master.Save()
    wb_master.Close(True)
    print("Plantilla maestra actualizada correctamente!")
    
except Exception as e:
    print(f"Error fatal copiando hojas: {e}")
finally:
    if excel:
        excel.Quit()
        print("Excel cerrado.")
