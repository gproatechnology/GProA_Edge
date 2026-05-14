import asyncio
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check():
    await udb._ensure_sqlite()
    
    projects = await udb.projects_find({})
    ejemplo4 = None
    for p in projects:
        if "ejemplo 4" in p.get("name", "").lower() or "ejemplo4" in p.get("name", "").lower():
            ejemplo4 = p
            break
            
    if not ejemplo4:
        print("Proyecto 'Ejemplo 4' no encontrado.")
        return

    print(f"Project found: {ejemplo4['name']} (ID: {ejemplo4['id']})")
    print(f"Project Efficiency: {ejemplo4.get('efficiency', 0)}%")
    
    files = await udb.files_find({"project_id": ejemplo4["id"]})
    print(f"\nTotal Files in 'Ejemplo 4': {len(files)}")
    
    processed_count = sum(1 for f in files if f.get("status") == "processed")
    error_count = sum(1 for f in files if f.get("status") == "error")
    pending_count = sum(1 for f in files if f.get("status") == "pending")
    
    print(f"- Processed: {processed_count}")
    print(f"- Error: {error_count}")
    print(f"- Pending: {pending_count}")
    
    for f in files:
        print(f"\n=========================================")
        print(f"Archivo: {f['filename']} | Estado: {f.get('status')}")
        print(f"Categoría: {f.get('category_edge')} | Medida: {f.get('measure_edge')} | Tipo Doc: {f.get('doc_type')}")
        
        if f.get('watts') is not None:
            print(f"-> Watts extraídos: {f.get('watts')}")
        if f.get('lumens') is not None:
            print(f"-> Lúmenes extraídos: {f.get('lumens')}")
            
        spec_data = f.get('specialized_data')
        if spec_data:
            print(f"Datos Especializados:")
            out_str = json.dumps(spec_data, indent=2, ensure_ascii=False)
            if len(out_str) > 500:
                print(out_str[:500] + "\n... [TRUNCADO]")
            else:
                print(out_str)
        if f.get('error_msg'):
            print(f"Error: {f.get('error_msg')}")

if __name__ == "__main__":
    asyncio.run(check())
