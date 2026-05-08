from fastapi import FastAPI
from fastapi.responses import FileResponse as StarletteFileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from app.core.config import ROOT_DIR, MONGO_URL, logger
from app.db.database import udb, client
from app.api.api_router import api_router

app = FastAPI(title="EDGE Document Processor API v2")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Include API Router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    import asyncio
    # from app.db.seed import seed_demo_data
    # Desactivado para producción:
    # asyncio.create_task(seed_demo_data())
    pass

origins = os.environ.get('CORS_ORIGINS', '*').split(',')
allow_credentials = True
if '*' in origins:
    allow_credentials = False

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=allow_credentials,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Static Files
frontend_build_dir = ROOT_DIR.parent / "frontend" / "build"
if frontend_build_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_build_dir / "static")), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        try:
            path_to_file = frontend_build_dir / full_path
            if path_to_file.is_file():
                return StarletteFileResponse(str(path_to_file))
            
            index_file = frontend_build_dir / "index.html"
            if index_file.is_file():
                return StarletteFileResponse(str(index_file))
            
            return {"error": "Frontend build/index.html not found."}, 404
        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500
else:
    logger.warning("Frontend build directory not found. API only mode.")

@app.on_event("shutdown")
async def shutdown_db():
    if MONGO_URL and client:
        client.close()
        logger.info("MongoDB connection closed")
    elif udb.conn:
        await udb.conn.close()
        logger.info("SQLite connection closed")

@app.get("/api")
async def root():
    return {"message": "EDGE Document Processor API v2"}
