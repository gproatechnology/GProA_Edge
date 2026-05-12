import os
import json
import logging
import io
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.core.config import ROOT_DIR, logger
from app.db.database import udb

# Allow insecure transport for local development (http instead of https)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

class GoogleDriveService:
    def __init__(self):
        self.creds_path = ROOT_DIR / 'data' / 'credentials.json'

    def get_flow(self, redirect_uri: str, state: Optional[str] = None):
        """Creates a flow instance for OAuth2."""
        from google_auth_oauthlib.flow import Flow
        logger.info(f"Creating OAuth flow with redirect_uri: {redirect_uri}")
        logger.info(f"Using credentials file: {self.creds_path}")
        if not os.path.exists(self.creds_path):
            logger.error(f"Credentials file NOT FOUND at: {self.creds_path}")
            raise FileNotFoundError(f"No se encuentra credentials.json en {self.creds_path}")
            
        return Flow.from_client_secrets_file(
            str(self.creds_path),
            scopes=SCOPES,
            redirect_uri=redirect_uri,
            state=state
        )

    async def get_user_credentials(self, user_id: str) -> Optional[Any]:
        """Gets valid user credentials from the database."""
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        token_data = await udb.google_tokens_find_one(user_id)
        if not token_data:
            return None
        
        creds = Credentials.from_authorized_user_info(json.loads(token_data['token_json']), SCOPES)
        
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token
                await udb.google_tokens_upsert(user_id, creds.to_json())
            except Exception as e:
                logger.error(f"Error refreshing token for user {user_id}: {e}")
                return None
        
        return creds

    async def save_user_token(self, user_id: str, token_json: str):
        """Saves a user's token to the unified database."""
        try:
            # Ensure table exists before saving
            if hasattr(udb, '_ensure_sqlite'):
                await udb._ensure_sqlite()
            await udb.google_tokens_upsert(user_id, token_json)
            logger.info(f"Token saved/updated for user: {user_id}")
        except Exception as e:
            logger.error(f"Error saving user token: {e}")
            raise e

    async def list_files(self, user_id: str, folder_id: str = 'root', recursive: bool = False) -> List[Dict[str, Any]]:
        """Lists files in a specific folder, optionally recursive."""
        from googleapiclient.discovery import build
        creds = await self.get_user_credentials(user_id)
        if not creds:
            logger.warning(f"No credentials found for user {user_id}")
            return []

        try:
            service = build('drive', 'v3', credentials=creds)
            query = f"'{folder_id}' in parents and trashed = false"
            results = service.files().list(
                q=query, 
                fields="nextPageToken, files(id, name, mimeType, size)"
            ).execute()
            
            files = results.get('files', [])
            all_files = []

            for f in files:
                if f['mimeType'] == 'application/vnd.google-apps.folder':
                    f['is_folder'] = True
                    all_files.append(f)
                    if recursive:
                        sub_files = await self.list_files(user_id, f['id'], recursive=True)
                        # Add prefix to sub-files names for clarity during flat listing
                        for sf in sub_files:
                            if not sf.get('is_folder'):
                                sf['parent_name'] = f['name']
                                all_files.append(sf)
                else:
                    f['is_folder'] = False
                    all_files.append(f)

            return all_files
        except Exception as e:
            logger.error(f"Error listing files from Drive for user {user_id}: {e}")
            return []

    async def download_file(self, user_id: str, file_id: str, dest_path: str) -> bool:
        """Downloads a file from Drive for a specific user."""
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        creds = await self.get_user_credentials(user_id)
        if not creds:
            return False

        try:
            service = build('drive', 'v3', credentials=creds)
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            with open(dest_path, 'wb') as f:
                f.write(fh.getbuffer())
            return True
        except Exception as e:
            logger.error(f"Error downloading file {file_id} for user {user_id}: {e}")
            return False

    async def sync_folder(self, user_id: str, folder_id: str, project_id: str) -> List[str]:
        """Syncs all relevant files recursively from a Drive folder."""
        # Get all files recursively
        files = await self.list_files(user_id, folder_id, recursive=True)
        downloaded_files = []
        
        upload_dir = ROOT_DIR / 'uploads' / project_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            if file.get('is_folder'):
                continue
                
            # Simple filter for relevant files
            name = file['name'].lower()
            if any(name.endswith(ext) for ext in ['.pdf', '.xlsx', '.dxf', '.dwg']):
                # Maintain folder structure in local uploads if parent_name exists
                target_dir = upload_dir
                if file.get('parent_name'):
                    target_dir = upload_dir / file['parent_name']
                    target_dir.mkdir(parents=True, exist_ok=True)
                
                dest = target_dir / file['name']
                if await self.download_file(user_id, file['id'], str(dest)):
                    # 1. Create DB entry for the file
                    import uuid
                    file_id = str(uuid.uuid4())
                    file_doc = {
                        "id": file_id,
                        "project_id": project_id,
                        "filename": file['name'],
                        "file_size": int(file.get('size', 0)),
                        "file_path": str(dest),
                        "status": "pending",
                        "uploaded_at": datetime.datetime.now().isoformat()
                    }
                    await udb.files_insert_one(file_doc)
                    
                    # 2. Trigger Audit (Background-ish)
                    try:
                        from app.services.audit_service import audit_service
                        await audit_service.process_file(file_id)
                    except Exception as e:
                        logger.error(f"Post-sync audit failed for {file['name']}: {e}")
                    
                    downloaded_files.append(f"{file.get('parent_name', '')}/{file['name']}" if file.get('parent_name') else file['name'])
        
        # Log the sync action
        import uuid
        import datetime
        sync_log = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "user_id": user_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "files_synced": downloaded_files,
            "status": "success" if downloaded_files else "no_files"
        }
        await udb.sync_logs_insert(sync_log)
        
        return downloaded_files

google_drive_service = GoogleDriveService()
