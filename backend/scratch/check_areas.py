import sqlite3
import json

db_path = "c:/Users/X1/OneDrive/Documentos/Python_VS Code/GProA/GProA_EOSIS_Edge/backend/data/gproa_edge.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT filename, areas, specialized_data FROM files WHERE project_id='ceaebf11-b317-4d41-86cc-d64edcd1fbe3'")
for row in cur.fetchall():
    filename, areas, spec = row
    print(f"--- {filename} ---")
    print(f"Areas: {areas[:200] if areas else 'None'}")
    print(f"Spec: {spec[:200] if spec else 'None'}")
conn.close()
