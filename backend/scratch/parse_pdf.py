import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.parsers.pdf_parser import PDFParser

async def test_parse():
    file_path = r"c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\docs\Documentos_EOSIS\03_EEM22_Efficient_Lighting\24044EL100.pdf"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    parser = PDFParser()
    data = parser.parse(file_path)
    
    print("=== Extracted Text Length ===")
    text = data.get("content_text", "")
    print(len(text))
    
    print("\n=== First 1000 characters ===")
    print(text[:1000])

if __name__ == "__main__":
    asyncio.run(test_parse())
