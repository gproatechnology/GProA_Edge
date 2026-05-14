import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check():
    await udb._ensure_sqlite()
    
    # 1. Find the project "Ejemplo 2"
    projects = await udb.projects_find({})
    ejemplo2 = None
    for p in projects:
        if "ejemplo 2" in p.get("name", "").lower() or "ejemplo2" in p.get("name", "").lower():
            ejemplo2 = p
            break
            
    if not ejemplo2:
        print("Proyecto 'Ejemplo 2' no encontrado en la base de datos.")
        # Try to find recent files instead
        files = await udb.files_find({})
        print(f"Total files in DB: {len(files)}")
        return

    print(f"Project found: {ejemplo2['name']} (ID: {ejemplo2['id']})")
    
    # 2. Get files for this project
    files = await udb.files_find({"project_id": ejemplo2["id"]})
    print(f"\nFiles found: {len(files)}")
    
    for f in files:
        if f['filename'].lower().endswith('.pdf'):
            print(f"\n--- PDF: {f['filename']} ---")
            print(f"Status: {f.get('status')}")
            print(f"Category: {f.get('category_edge')}")
            print(f"Measure: {f.get('measure_edge')}")
            
            spec_data = f.get('specialized_data')
            if spec_data:
                import json
                print("Specialized Data:")
                print(json.dumps(spec_data, indent=2, ensure_ascii=False))
            else:
                print("No specialized data found.")

if __name__ == "__main__":
    asyncio.run(check())
