import fitz
import os

pdf_path = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\docs\Documentos_EOSIS\03_EEM22_Efficient_Lighting\24044EL100.pdf"
output_path = r"c:\Users\X1\.gemini\antigravity\brain\a15bc122-e1d9-4a97-b907-ba2bed23f953\diagrama_vista_ia.png"

try:
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    pix.save(output_path)
    print(f"Imagen guardada en: {output_path}")
except Exception as e:
    print(f"Error: {e}")
