import asyncio
import os
import sys
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.assistant_service import get_assistant_response
from app.db.database import udb

async def check():
    await udb._ensure_sqlite()
    
    # Get project id for Ejemplo 5
    projects = await udb.projects_find({})
    project_id = None
    for p in projects:
        if "ejemplo 5" in p.get("name", "").lower():
            project_id = p["id"]
            break
            
    if not project_id:
        print("Project not found")
        return
        
    print(f"Testing chat with project_id={project_id}")
    try:
        res = await get_assistant_response(project_id, "hola")
        print("Response:", res)
    except Exception as e:
        print("Exception caught in script:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check())
