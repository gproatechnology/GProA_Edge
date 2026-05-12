from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from typing import List, Dict, Any
from app.services.google_drive_service import google_drive_service
from app.db.database import udb
import os
import json
from app.core.config import ROOT_DIR, logger

router = APIRouter()

@router.get("/status/{user_id}")
async def get_drive_status(user_id: str):
    """Checks if Google Drive is connected for a specific user."""
    creds = await google_drive_service.get_user_credentials(user_id)
    creds_exists = os.path.exists(ROOT_DIR / 'data' / 'credentials.json')
    
    return {
        "connected": creds is not None,
        "credentials_configured": creds_exists,
        "message": "Conectado" if creds else "No conectado"
    }

@router.get("/logs/{project_id}")
async def get_sync_logs(project_id: str):
    """Retrieves sync logs for a project."""
    try:
        logs = await udb.sync_logs_find({"project_id": project_id})
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth-url")
async def get_auth_url(user_id: str, redirect_uri: str):
    """Generates the Google OAuth2 authorization URL."""
    try:
        flow = google_drive_service.get_flow(redirect_uri)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return {"auth_url": authorization_url, "state": state}
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def oauth2_callback(code: str, user_id: str, redirect_uri: str):
    """Handles the OAuth2 callback and saves the token."""
    try:
        flow = google_drive_service.get_flow(redirect_uri)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        await google_drive_service.save_user_token(user_id, credentials.to_json())
        return {"status": "success", "message": "Token guardado correctamente"}
    except Exception as e:
        logger.error(f"Error in OAuth2 callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{user_id}")
async def list_drive_files(user_id: str, folder_id: str = 'root'):
    """Lists files from Google Drive with automatic classification."""
    try:
        files = await google_drive_service.list_files(user_id, folder_id)
        
        # Add classification logic
        classified_files = []
        for file in files:
            name = file['name'].lower()
            category = "Documento"
            resource = "General"
            
            if name.endswith('.dxf') or name.endswith('.dwg'):
                category = "Plano CAD"
                resource = "Geometría/Áreas"
            elif 'agua' in name or 'water' in name or 'hidro' in name:
                category = "Cálculo"
                resource = "EDGE Agua"
            elif 'ener' in name or 'luz' in name or 'ilum' in name:
                category = "Cálculo"
                resource = "EDGE Energía"
            elif 'mat' in name or 'estruc' in name:
                category = "Cálculo"
                resource = "EDGE Materiales"
            
            file['suggested_category'] = category
            file['edge_resource'] = resource
            classified_files.append(file)
            
        return {"files": classified_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/{project_id}")
async def sync_project_drive(project_id: str, user_id: str, folder_id: str):
    """Syncs files from a Drive folder to a project for a specific user."""
    try:
        files = await google_drive_service.sync_folder(user_id, folder_id, project_id)
        return {
            "status": "success",
            "message": f"Se han sincronizado {len(files)} archivos.",
            "synced_files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
