from fastapi import APIRouter
from app.api.endpoints import projects, files, processing, rules, analysis, exports, debug, assistant, google_drive

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(files.router, tags=["files"])
api_router.include_router(processing.router, tags=["processing"])
api_router.include_router(rules.router, tags=["rules"])
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(exports.router, tags=["exports"])
api_router.include_router(assistant.router, tags=["assistant"])
api_router.include_router(google_drive.router, prefix="/google-drive", tags=["google-drive"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
