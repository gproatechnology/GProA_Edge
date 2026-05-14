import sqlite3
import json

db_path = "c:/Users/X1/OneDrive/Documentos/Python_VS Code/GProA/GProA_EOSIS_Edge/backend/data/gproa_edge.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT project_id, filename, status FROM files ORDER BY uploaded_at DESC LIMIT 10")
files = cur.fetchall()
print("Recent files globally:")
for f in files:
    print(f)

cur.execute("SELECT filename, status FROM files WHERE project_id='ceaebf11-b317-4d41-86cc-d64edcd1fbe3'")
project_files = cur.fetchall()
print("\nFiles for specific project (ceaebf11-b317-4d41-86cc-d64edcd1fbe3):")
for f in project_files:
    print(f)

conn.close()
