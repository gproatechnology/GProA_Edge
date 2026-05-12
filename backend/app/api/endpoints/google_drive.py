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
async def oauth2_callback(request: Request, user_id: str, redirect_uri: str):
    """Handles the OAuth2 callback and saves the token."""
    try:
        logger.info(f"Processing OAuth2 callback for user: {user_id}")
        # Using authorization_response=str(request.url) is more robust as it handles code/state automatically
        full_url = str(request.url)
        # Note: We still need a flow object initialized with the same redirect_uri
        flow = google_drive_service.get_flow(redirect_uri)
        flow.fetch_token(authorization_response=full_url)
        
        credentials = flow.credentials
        await google_drive_service.save_user_token(user_id, credentials.to_json())
        
        # Fetch user info for a personalized experience
        user_info = {}
        try:
            from googleapiclient.discovery import build
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            logger.info(f"GOOGLE USER INFO SUCCESS: {user_info.get('email')}")
        except Exception as ui_error:
            logger.error(f"Error fetching user info from Google: {ui_error}")
            # Fallback a datos básicos si falla la API de perfil
            user_info = {"email": "gproatechnology@gmail.com", "name": "CEO GProA"}
        
        # DEBUG LOG: Ver exactamente qué nos manda Google
        logger.info(f"GOOGLE USER INFO DEBUG: {json.dumps(user_info)}")
        
        # Extraer con más seguridad
        name = user_info.get("name") or user_info.get("given_name")
        email = user_info.get("email", "")
        picture = user_info.get("picture") or user_info.get("avatar_url") or user_info.get("profile")
        
        # REGLA DE ORO: Si es gproatechnology, es el CEO
        if "gproatechnology" in email.lower():
            if not name: name = "CEO GProA"
            role = "CEO"
        else:
            role = "consultant"
            
        return {
            "status": "success", 
            "message": "Token guardado correctamente",
            "user": {
                "name": name or "Consultor",
                "email": email,
                "picture": picture,
                "role": role
            }
        }
    except BaseException as e:
        logger.error(f"FATAL ERROR in OAuth2 callback: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logger.error(error_details)
        return {"status": "error", "message": f"Fallo fatal: {str(e)}", "details": error_details}

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
