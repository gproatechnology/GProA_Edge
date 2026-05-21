import asyncio
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check_latest_result():
    await udb._ensure_sqlite()
    
    # Find the specific file
    f = await udb.files_find_one({"filename": "24044EL100.pdf"})
    
    if not f:
        print("No se encontró el archivo 24044EL100.pdf en la base de datos.")
        return
        
    print(f"\n{'='*50}")
    print(f"Archivo: {f.get('filename')}")
    print(f"Estado: {f.get('status')}")
    print(f"Watts Totales Extraídos: {f.get('watts')}")
    
    spec_data = f.get('specialized_data', {})
    print("\n--- Specialized Data (Nueva Lógica) ---")
    if spec_data:
        print(json.dumps(spec_data, indent=2, ensure_ascii=False))
    else:
        print("No specialized data found.")
            
if __name__ == "__main__":
    asyncio.run(check_latest_result())
