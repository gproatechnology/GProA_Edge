import json
from app.core.config import MONGO_URL, DB_NAME, ROOT_DIR

db = None
client = None
if MONGO_URL:
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
else:
    import aiosqlite
    DATA_DIR = ROOT_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)
    DB_PATH = DATA_DIR / f"{DB_NAME}.db"

class UnifiedDB:
    """Wrapper that provides same interface for MongoDB and SQLite."""

    def __init__(self):
        self.mode = "mongodb" if MONGO_URL else "sqlite"
        self.conn = None  # Lazy-init on first use
        # Render support: use a persistent path if provided
        sqlite_custom_path = os.getenv("SQLITE_PATH")
        if sqlite_custom_path:
            self.sqlite_path = sqlite_custom_path
        else:
            self.sqlite_path = DB_PATH
        
        logger.info(f"Database mode: {self.mode}")

    async def _ensure_sqlite(self):
        """Initialize SQLite connection and schema on first use."""
        if self.conn is None:
            print(">>> Initializing SQLite connection...")
            self.conn = await aiosqlite.connect(self.sqlite_path)
            self.conn.row_factory = aiosqlite.Row
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    typology TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    file_count INTEGER DEFAULT 0,
                    processed_count INTEGER DEFAULT 0,
                    priority TEXT,
                    square_meters REAL,
                    annual_consumption_kwh REAL
                )
            """)
            # Migracion automatica para bases de datos existentes
            for col, col_type in [("priority", "TEXT"), ("square_meters", "REAL"), ("annual_consumption_kwh", "REAL")]:
                try:
                    await self.conn.execute(f"ALTER TABLE projects ADD COLUMN {col} {col_type}")
                except:
                    pass # La columna ya existe
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    content_text TEXT,
                    status TEXT DEFAULT 'pending',
                    category_edge TEXT,
                    measure_edge TEXT,
                    doc_type TEXT,
                    confidence REAL,
                    watts REAL,
                    lumens REAL,
                    tipo_equipo TEXT,
                    marca TEXT,
                    modelo TEXT,
                    areas TEXT,
                    specialized_data TEXT,
                    uploaded_at TEXT NOT NULL
                )
            """)
            await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id)")
            await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
            await self.conn.commit()
            print(">>> SQLite database ready")

    async def projects_insert_one(self, doc: dict):
        if self.mode == "mongodb":
            await db.projects.insert_one(doc)
        else:
            await self._ensure_sqlite()
            await self.conn.execute("""
                INSERT INTO projects (id, name, typology, created_at, file_count, processed_count, priority, square_meters, annual_consumption_kwh)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["id"], doc["name"], doc["typology"], doc["created_at"],
                doc.get("file_count", 0), doc.get("processed_count", 0),
                doc.get("priority"), doc.get("square_meters"), doc.get("annual_consumption_kwh")
            ))
            await self.conn.commit()

    async def projects_find_one(self, query: dict, projection: dict = None):
        if self.mode == "mongodb":
            proj = {k: 1 for k in projection.keys()} if projection else None
            return await db.projects.find_one(query, proj)
        else:
            await self._ensure_sqlite()
            columns = ["id", "name", "typology", "created_at", "file_count", "processed_count", "priority", "square_meters", "annual_consumption_kwh"]
            where = [f"{k}=?" for k in query.keys()]
            params = list(query.values())
            sql = f"SELECT {', '.join(columns)} FROM projects WHERE {' AND '.join(where)}"
            async with self.conn.execute(sql, params) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def projects_find(self, query: dict = None, projection: dict = None):
        if self.mode == "mongodb":
            proj = {k: 1 for k in projection.keys()} if projection else None
            cursor = db.projects.find(query or {}, proj or {})
            return await cursor.to_list(100)
        else:
            await self._ensure_sqlite()
            columns = ["id", "name", "typology", "created_at", "file_count", "processed_count", "priority", "square_meters", "annual_consumption_kwh"]
            sql = f"SELECT {', '.join(columns)} FROM projects"
            params = []
            if query:
                where = [f"{k}=?" for k in query.keys()]
                params = list(query.values())
                sql += " WHERE " + " AND ".join(where)
            async with self.conn.execute(sql, params) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def projects_delete_one(self, query: dict):
        if self.mode == "mongodb":
            return await db.projects.delete_one(query)
        else:
            await self._ensure_sqlite()
            where = [f"{k}=?" for k in query.keys()]
            params = list(query.values())
            sql = f"DELETE FROM projects WHERE {' AND '.join(where)}"
            async with self.conn.execute(sql, params) as cur:
                await self.conn.commit()
                return type('Result', (), {'deleted_count': cur.rowcount})()

    async def projects_update_one(self, query: dict, update: dict):
        if self.mode == "mongodb":
            await db.projects.update_one(query, update)
        else:
            await self._ensure_sqlite()
            set_clause = [f"{k}=?" for k in update["$set"].keys()]
            where_clause = [f"{k}=?" for k in query.keys()]
            params = list(update["$set"].values()) + list(query.values())
            sql = f"UPDATE projects SET {', '.join(set_clause)} WHERE {' AND '.join(where_clause)}"
            await self.conn.execute(sql, params)
            await self.conn.commit()

    async def projects_delete_many(self, query: dict):
        if self.mode == "mongodb":
            await db.projects.delete_many(query)
        else:
            await self._ensure_sqlite()
            if not query:
                await self.conn.execute("DELETE FROM projects")
            else:
                where = [f"{k}=?" for k in query.keys()]
                params = list(query.values())
                sql = f"DELETE FROM projects WHERE {' AND '.join(where)}"
                await self.conn.execute(sql, params)
            await self.conn.commit()

    async def files_insert_one(self, doc: dict):
        if self.mode == "mongodb":
            await db.files.insert_one(doc)
        else:
            await self._ensure_sqlite()
            areas = json.dumps(doc.get("areas")) if doc.get("areas") else None
            specialized = json.dumps(doc.get("specialized_data")) if doc.get("specialized_data") else None
            await self.conn.execute("""
                INSERT INTO files (
                    id, project_id, filename, file_size, content_text, status,
                    category_edge, measure_edge, doc_type, confidence,
                    watts, lumens, tipo_equipo, marca, modelo,
                    areas, specialized_data, uploaded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["id"], doc["project_id"], doc["filename"], doc["file_size"],
                doc.get("content_text"), doc.get("status", "pending"),
                doc.get("category_edge"), doc.get("measure_edge"), doc.get("doc_type"),
                doc.get("confidence"),
                doc.get("watts"), doc.get("lumens"), doc.get("tipo_equipo"),
                doc.get("marca"), doc.get("modelo"),
                areas, specialized, doc.get("uploaded_at")
            ))
            await self.conn.commit()

    async def files_find_one(self, query: dict, projection: dict = None):
        if self.mode == "mongodb":
            proj = {k: 1 for k in projection.keys()} if projection else None
            return await db.files.find_one(query, proj)
        else:
            await self._ensure_sqlite()
            columns = ["id", "project_id", "filename", "file_size", "content_text", "status",
                       "category_edge", "measure_edge", "doc_type", "confidence",
                       "watts", "lumens", "tipo_equipo", "marca", "modelo",
                       "areas", "specialized_data", "uploaded_at"]
            if projection and "content_text" in projection and projection["content_text"] == 0:
                columns = [c for c in columns if c != "content_text"]
            where = [f"{k}=?" for k in query.keys()]
            params = list(query.values())
            sql = f"SELECT {', '.join(columns)} FROM files WHERE {' AND '.join(where)}"
            async with self.conn.execute(sql, params) as cur:
                row = await cur.fetchone()
                if row:
                    return self._deserialize_file_row(dict(row))
            return None

    async def files_find(self, query: dict = None, projection: dict = None):
        if self.mode == "mongodb":
            proj = {k: 1 for k in projection.keys()} if projection else None
            cursor = db.files.find(query or {}, proj or {})
            return await cursor.to_list(500)
        else:
            await self._ensure_sqlite()
            columns = ["id", "project_id", "filename", "file_size", "status",
                       "category_edge", "measure_edge", "doc_type", "confidence",
                       "watts", "lumens", "tipo_equipo", "marca", "modelo",
                       "areas", "specialized_data", "uploaded_at"]
            if projection and "content_text" in projection and projection["content_text"] == 0:
                columns = [c for c in columns if c != "content_text"]
            sql = f"SELECT {', '.join(columns)} FROM files"
            params = []
            if query:
                where = [f"{k}=?" for k in query.keys()]
                params = list(query.values())
                sql += " WHERE " + " AND ".join(where)
            async with self.conn.execute(sql, params) as cur:
                rows = await cur.fetchall()
                return [self._deserialize_file_row(dict(r)) for r in rows]

    def _deserialize_file_row(self, row: dict) -> dict:
        if "areas" in row and row["areas"]:
            try:
                row["areas"] = json.loads(row["areas"])
            except:
                row["areas"] = None
        if "specialized_data" in row and row["specialized_data"]:
            try:
                row["specialized_data"] = json.loads(row["specialized_data"])
            except:
                row["specialized_data"] = None
        return row

    async def files_update_one(self, query: dict, update: dict):
        if self.mode == "mongodb":
            await db.files.update_one(query, update)
        else:
            await self._ensure_sqlite()
            set_dict = update.get("$set", {})
            if "areas" in set_dict and isinstance(set_dict["areas"], list):
                set_dict["areas"] = json.dumps(set_dict["areas"])
            if "specialized_data" in set_dict and isinstance(set_dict["specialized_data"], dict):
                set_dict["specialized_data"] = json.dumps(set_dict["specialized_data"])
            set_clause = ", ".join([f"{k}=?" for k in set_dict.keys()])
            params = list(set_dict.values())
            where = [f"{k}=?" for k in query.keys()]
            params.extend(list(query.values()))
            sql = f"UPDATE files SET {set_clause} WHERE {' AND '.join(where)}"
            async with self.conn.execute(sql, params) as cur:
                await self.conn.commit()

    async def files_delete_one(self, query: dict):
        if self.mode == "mongodb":
            return await db.files.delete_one(query)
        else:
            await self._ensure_sqlite()
            where = [f"{k}=?" for k in query.keys()]
            params = list(query.values())
            sql = f"DELETE FROM files WHERE {' AND '.join(where)}"
            async with self.conn.execute(sql, params) as cur:
                await self.conn.commit()
                return type('Result', (), {'deleted_count': cur.rowcount})()

    async def files_delete_many(self, query: dict):
        if self.mode == "mongodb":
            await db.files.delete_many(query)
        else:
            await self._ensure_sqlite()
            if not query:
                sql = "DELETE FROM files"
                params = []
            else:
                where = [f"{k}=?" for k in query.keys()]
                params = list(query.values())
                sql = f"DELETE FROM files WHERE {' AND '.join(where)}"
            
            await self.conn.execute(sql, params)
            await self.conn.commit()

    async def files_count_documents(self, query: dict):
        if self.mode == "mongodb":
            return await db.files.count_documents(query)
        else:
            await self._ensure_sqlite()
            where = [f"{k}=?" for k in query.keys()]
            params = list(query.values())
            sql = f"SELECT COUNT(*) as cnt FROM files WHERE {' AND '.join(where)}"
            async with self.conn.execute(sql, params) as cur:
                row = await cur.fetchone()
                return row["cnt"] if row else 0

# Initialize unified DB
udb = UnifiedDB()
