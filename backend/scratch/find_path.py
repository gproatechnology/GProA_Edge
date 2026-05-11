import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.db.database import udb

async def find_file_path():
    files = await udb.files_find({"filename": "24044A700.dxf"})
    if files:
        f = files[-1]
        print(f"File found: {f['filename']} -> Path ID: {f['id']}")
        uploads_dir = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads'
        real_path = os.path.join(uploads_dir, f"{f['id']}.dxf")
        print(f"Real path: {real_path}")
        if os.path.exists(real_path):
            print("Path exists!")
        else:
            print("Path does NOT exist at expected ID location.")

if __name__ == "__main__":
    asyncio.run(find_file_path())
