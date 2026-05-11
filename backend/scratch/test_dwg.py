import sys
import os

# Add backend to sys.path
sys.path.append(r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend')

from app.services.parsers.cad_parser import CADParser

def test_dwg_parsing():
    parser = CADParser()
    file_path = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads\9aceb98a-9bc6-44d3-9f51-f2f40b5961ca.dwg'
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Parsing file: {file_path}")
    result = parser.parse(file_path)
    
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_dwg_parsing()
