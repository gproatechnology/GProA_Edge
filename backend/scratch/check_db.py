import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check_db():
    await udb._ensure_sqlite()
    files = await udb.files_find({})
    
    if not files:
        print("La base de datos de archivos está completamente VACÍA.")
    else:
        print(f"Hay {len(files)} archivos en la base de datos:")
        for f in files:
            print(f"- {f.get('filename')} (Proyecto: {f.get('project_id')})")

if __name__ == "__main__":
    asyncio.run(check_db())
