import asyncio
import os
import sys
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import udb

async def audit():
    print("\n" + "="*60)
    print("REPORTE DE AUDITORÍA INTEGRAL - GProA EDGE")
    print("="*60)
    
    # 1. Auditar Proyectos
    projects = await udb.projects_find({})
    print(f"\n>>> Proyectos en base de datos: {len(projects)}")
    for p in projects:
        print(f"ID: {p['id']} | Nombre: {p.get('name', 'N/A')} | Status: {p.get('status', 'N/A')}")

    # 2. Auditar Archivos
    files = await udb.files_find({})
    print(f"\n>>> Total de archivos: {len(files)}")
    
    for f in files:
        print(f"\nARCHIVO: {f['filename']}")
        print(f"PROJECT ID: {f.get('project_id')}")
        print(f"STATUS:     {f.get('status')}")
        print(f"CATEGORÍA:  {f.get('category_edge', 'PENDIENTE')}")
        
        data = f.get('specialized_data')
        if data:
            print("DATOS EXTRAÍDOS PRESENTE (OK)")
        else:
            print(">>> DATOS EXTRAÍDOS: VACÍO")
            
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(audit())
