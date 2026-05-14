import asyncio
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check():
    await udb._ensure_sqlite()
    
    projects = await udb.projects_find({})
    ejemplo5 = None
    for p in projects:
        if "ejemplo 5" in p.get("name", "").lower() or "ejemplo5" in p.get("name", "").lower():
            ejemplo5 = p
            break
            
    if not ejemplo5:
        print("Proyecto 'Ejemplo 5' no encontrado.")
        return

    print(f"Project found: {ejemplo5['name']} (ID: {ejemplo5['id']})")
    print(f"Project Efficiency: {ejemplo5.get('efficiency', 0)}%")
    
    files = await udb.files_find({"project_id": ejemplo5["id"]})
    print(f"\nTotal Files in 'Ejemplo 5': {len(files)}")
    
    processed_count = sum(1 for f in files if f.get("status") == "processed")
    error_count = sum(1 for f in files if f.get("status") == "error")
    pending_count = sum(1 for f in files if f.get("status") == "pending")
    
    print(f"- Processed: {processed_count}")
    print(f"- Error: {error_count}")
    print(f"- Pending: {pending_count}")
    
    # Mostrar solo algunos si son muchos (iluminación son 14)
    for f in files:
        if f.get('status') == 'error':
            print(f"\n[ERROR] Archivo: {f['filename']} | Error: {f.get('error_msg')}")
            
    print("\n--- Archivos Procesados Recientemente ---")
    processed_files = [f for f in files if f.get('status') == 'processed']
    for f in processed_files[-5:]: # solo ultimos 5 para no llenar
        print(f"\nArchivo: {f['filename']}")
        print(f"Categoría: {f.get('category_edge')} | Medida: {f.get('measure_edge')}")
        if f.get('watts') is not None:
            print(f"-> Watts extraídos: {f.get('watts')}")
        if f.get('lumens') is not None:
            print(f"-> Lúmenes extraídos: {f.get('lumens')}")
        
        spec = f.get('specialized_data')
        if spec:
            if spec.get('eficacia_global'):
                 print(f"-> Eficacia Global: {spec.get('eficacia_global')} lm/W")
            if spec.get('cumple_edge') is not None:
                 print(f"-> Cumple EDGE: {spec.get('cumple_edge')}")

if __name__ == "__main__":
    asyncio.run(check())
