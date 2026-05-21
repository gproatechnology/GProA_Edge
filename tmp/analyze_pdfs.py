import json, pathlib, sys
sys.path.append(r"C:/Users/X1/OneDrive/Documentos/Python_VS Code/GProA/GProA_EOSIS_Edge/backend/app")
from services.parsers.pdf_parser import PDFParser

def process(pdf_path):
    parser = PDFParser()
    result = parser.parse(pdf_path)
    summary = {
        "filename": pathlib.Path(pdf_path).name,
        "page_count": result.get("page_count"),
        "extracted_parameters": result.get("extracted_parameters"),
        "geometry": [{"page": g["page"], "vector_shapes": g["vector_shapes"], "detected_areas": len(g["detected_areas"]) } for g in result.get("geometry", [])],
        "tables_count": len(result.get("tables", [])),
        "detected_areas_text": result.get("text_summary", {}).get("detected_areas_from_text", [])[:5]
    }
    print(json.dumps(summary, ensure_ascii=False))

pdfs = [
    r"C:/Users/X1/OneDrive/Documentos/Python_VS Code/GProA/GProA_EOSIS_Edge/docs/Documentos_EOSIS/EEM22_Layout_CUU PV-03 Tristone.pdf",
    r"C:/Users/X1/OneDrive/Documentos/Python_VS Code/GProA/GProA_EOSIS_Edge/docs/Documentos_EOSIS/Tristone_Area Breakdown_Layout.pdf",
    r"C:/Users/X1/OneDrive/Documentos/Python_VS Code/GProA/GProA_EOSIS_Edge/docs/Documentos_EOSIS/Tristone_EEM01_WWR_Drawings-Elevations.pdf"
]
for p in pdfs:
    process(p)
