from fastapi import FastAPI
from fastapi.responses import FileResponse as StarletteFileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from app.core.config import ROOT_DIR, MONGO_URL, logger, CORS_ORIGINS
from app.db.database import udb, client
from app.api.api_router import api_router

app = FastAPI(title="EDGE Document Processor API v2")

# Setup CORS - Read from environment
if CORS_ORIGINS and CORS_ORIGINS != "*":
    origins = [o.strip() for o in CORS_ORIGINS.split(",")]
elif CORS_ORIGINS == "*":
    origins = ["*"]
else:
    origins = ["http://localhost:3000"]  # Default dev origin

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")

# Setup Static Files
# Render support: check for 'dist' (Vite) or 'build' (CRA)
frontend_build_dir = ROOT_DIR.parent / "frontend" / "dist"
if not frontend_build_dir.exists():
    frontend_build_dir = ROOT_DIR.parent / "frontend" / "build"

if frontend_build_dir.exists():
    # Mount static assets
    static_dir = frontend_build_dir / "static"
    if not static_dir.exists():
        # Vite puts everything in root or assets
        static_dir = frontend_build_dir / "assets"
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    if (frontend_build_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_build_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Prevent intercepting API calls
        if full_path.startswith("api"):
            return {"error": "API route not found"}, 404
            
        try:
            path_to_file = frontend_build_dir / full_path
            if path_to_file.is_file():
                return StarletteFileResponse(str(path_to_file))
            
            index_file = frontend_build_dir / "index.html"
            if index_file.is_file():
                return StarletteFileResponse(str(index_file))
            
            return {"error": "Frontend entry point not found."}, 404
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
