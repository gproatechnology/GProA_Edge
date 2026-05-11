import sys
import os
import asyncio
import json

# Add backend to sys.path
sys.path.append(r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend')

from app.services.parsers.cad_parser import CADParser
from app.services.parsers.docx_parser import DocxParser
from app.services.ai_service import process_single_file_pipeline

async def test_parsers():
    # 1. Test CAD Parser (Improved DWG heuristic)
    cad = CADParser()
    dwg_file = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads\9aceb98a-9bc6-44d3-9f51-f2f40b5961ca.dwg'
    if os.path.exists(dwg_file):
        print("Testing DWG Heuristic Parser...")
        res = cad.parse(dwg_file)
        print(f"Format: {res.get('format')}")
        print(f"Areas detected: {len(res.get('areas', []))}")
        if res.get('areas'):
            print(f"First area: {res['areas'][0]}")
    
    # 2. Test DOCX Parser (New)
    # Since we don't have a docx file, we'll just check if it imports and instantiates
    docx = DocxParser()
    print("DocxParser instantiated successfully.")

    # 3. Test Pipeline (Simulation)
    file_doc = {
        "id": "test-id",
        "filename": "9aceb98a-9bc6-44d3-9f51-f2f40b5961ca.dwg",
        "content_text": "LUMINARIA LED 36W AREA: 45.5 m2",
        "status": "pending"
    }
    # Mocking DB for the test
    import app.db.database as db
    original_update = db.udb.files_update_one
    async def mock_update(query, update):
        print(f"DB Update: {update}")
    db.udb.files_update_one = mock_update
    
    print("\nTesting Pipeline Simulation (DWG)...")
    try:
        # Note: This will try to call OpenAI if keys are present
        # If not, it will fallback to mocks
        res = await process_single_file_pipeline(file_doc)
        print(f"Pipeline Result: {res}")
    except Exception as e:
        print(f"Pipeline error (expected if no API key): {e}")
    
    db.udb.files_update_one = original_update

if __name__ == "__main__":
    asyncio.run(test_parsers())
