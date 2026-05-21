import asyncio
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check_results():
    await udb._ensure_sqlite()
    
    # Find all processed files
    files = await udb.files_find({"status": "processed"})
    
    if not files:
        print("No hay archivos procesados en la base de datos.")
        return
        
    for f in files:
        print(f"\n{'='*50}")
        print(f"Archivo: {f.get('filename')}")
        print(f"Medida EDGE: {f.get('measure_edge')}")
        print(f"Categoría: {f.get('category_edge')}")
        print(f"Watts extraidos: {f.get('watts')}")
        print(f"Lúmenes extraidos: {f.get('lumens')}")
        
        spec_data = f.get('specialized_data', {})
        print("\n--- Specialized Data ---")
        if spec_data:
            print(json.dumps(spec_data, indent=2, ensure_ascii=False))
        else:
            print("No specialized data found.")
            
if __name__ == "__main__":
    asyncio.run(check_results())
