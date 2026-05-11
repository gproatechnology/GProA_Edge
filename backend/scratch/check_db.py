import asyncio
import os
import sys
import json

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.database import udb

async def check_new_project():
    projects = await udb.projects_find({})
    latest_project = projects[-1]
    print(f"Latest Project: {latest_project.get('name')}")
    
    files = await udb.files_find({"project_id": latest_project.get('id')})
    
    for f in files:
        print(f"\n--- {f.get('filename')} ---")
        print(f"Category: {f.get('category_edge')}")
        
        areas = f.get('areas', [])
        if areas:
            print(f"Areas ({len(areas)}):")
            for a in areas[:10]:
                print(f"  - {a.get('nombre')}: {a.get('area_m2')} m2")
        else:
            print("No areas detected in this file.")

if __name__ == "__main__":
    asyncio.run(check_new_project())
