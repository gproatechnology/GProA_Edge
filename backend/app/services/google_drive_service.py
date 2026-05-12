import os
import json
import logging
from typing import List, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from pathlib import Path
from app.core.config import ROOT_DIR, logger
from app.db.database import udb

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveService:
    def __init__(self):
        self.creds_path = ROOT_DIR / 'data' / 'credentials.json'

    def get_flow(self, redirect_uri: str):
        """Creates a flow instance for OAuth2."""
        return Flow.from_client_secrets_file(
            str(self.creds_path),
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )

    async def get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Gets valid user credentials from the database."""
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

    async def save_user_token(self, user_id: str, credentials_json: str):
        """Saves user token to the database."""
        await udb.google_tokens_upsert(user_id, credentials_json)

    async def list_files(self, user_id: str, folder_id: str = 'root') -> List[Dict[str, Any]]:
        """Lists files in a specific folder for a specific user."""
        creds = await self.get_user_credentials(user_id)
        if not creds:
            logger.warning(f"No credentials found for user {user_id}")
            return []

        try:
            service = build('drive', 'v3', credentials=creds)
            query = f"'{folder_id}' in parents and trashed = false"
            results = service.files().list(
                q=query,
                pageSize=100, 
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            logger.error(f"Error listing files from Drive for user {user_id}: {e}")
            return []

    async def download_file(self, user_id: str, file_id: str, dest_path: str) -> bool:
        """Downloads a file from Drive for a specific user."""
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
        """Syncs all relevant files from a Drive folder to the project uploads."""
        files = await self.list_files(user_id, folder_id)
        downloaded_files = []
        
        upload_dir = ROOT_DIR / 'uploads' / project_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            # Simple filter for relevant files
            name = file['name'].lower()
            if any(name.endswith(ext) for ext in ['.pdf', '.xlsx', '.dxf', '.dwg']):
                dest = upload_dir / file['name']
                if await self.download_file(user_id, file['id'], str(dest)):
                    downloaded_files.append(file['name'])
        
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

google_drive_service = GoogleDriveService()
