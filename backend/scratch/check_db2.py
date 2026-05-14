import sqlite3

db_path = "c:/Users/X1/OneDrive/Documentos/Python_VS Code/GProA/GProA_EOSIS_Edge/backend/data/gproa_edge.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, filename FROM files WHERE project_id='ceaebf11-b317-4d41-86cc-d64edcd1fbe3'")
for r in cur.fetchall():
    print(r)
conn.close()
