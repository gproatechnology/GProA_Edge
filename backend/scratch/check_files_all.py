import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.database import udb

async def check_files():
    await udb._ensure_sqlite()
    files = await udb.files_find({})
    print(f"Total archivos en DB: {len(files)}")
    for f in files:
        print(f"- {f.get('filename')} (Status: {f.get('status')}, Measure: {f.get('measure_edge')})")

if __name__ == "__main__":
    asyncio.run(check_files())
