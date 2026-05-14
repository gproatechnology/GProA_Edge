import asyncio
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check():
    await udb._ensure_sqlite()
    
    projects = await udb.projects_find({})
    ejemplo3 = None
    for p in projects:
        if "ejemplo 3" in p.get("name", "").lower() or "ejemplo3" in p.get("name", "").lower():
            ejemplo3 = p
            break
            
    if not ejemplo3:
        print("Proyecto 'Ejemplo 3' no encontrado.")
        return

    print(f"Project found: {ejemplo3['name']} (ID: {ejemplo3['id']})")
    
    files = await udb.files_find({"project_id": ejemplo3["id"]})
    print(f"\nTotal Files in 'Ejemplo 3': {len(files)}")
    
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
            # Solo mostrar los primeros 300 caracteres para no llenar la consola si es un CAD gigante
            out_str = json.dumps(spec_data, indent=2, ensure_ascii=False)
            if len(out_str) > 500:
                print(out_str[:500] + "\n... [TRUNCADO]")
            else:
                print(out_str)
        if f.get('error_msg'):
            print(f"Error: {f.get('error_msg')}")

if __name__ == "__main__":
    asyncio.run(check())
