from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
import uuid
import asyncio
import os
import logging
import magic
from datetime import datetime, timezone
from app.db.database import udb
from app.schemas.schemas import FileResponse, FileUpdate
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# Create limiter for this module
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".dxf", ".dwg", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/dxf",
    "application/octet-stream",  # DWG fallback
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",  # XLSX/DOCX fallback on some systems
    "text/plain",  # Minimal test content
    "application/x-empty",  # Empty files
}


def validate_file_upload(filename: str, content: bytes) -> tuple[bool, str]:
    """Validate file by extension and MIME type. Returns (is_valid, error_message)."""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Rejected upload - invalid extension: {ext} from {filename}")
        return False, f"File extension '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    if len(content) > MAX_FILE_SIZE:
        logger.warning(f"Rejected upload - size {len(content)} exceeds {MAX_FILE_SIZE}")
        return False, f"File size {len(content)} exceeds maximum {MAX_FILE_SIZE}"
    
    try:
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(content[:1024])
        
        # Allow application/octet-stream for DWG files (common case)
        if detected_mime not in ALLOWED_MIME_TYPES:
            # Double-check: some valid files may be detected as octet-stream
            if detected_mime == "application/octet-stream" and ext in {".dwg", ".dxf"}:
                return True, ""
            logger.warning(f"MIME mismatch: detected {detected_mime} for {filename}")
            return False, f"File content type mismatch. Detected: {detected_mime}"
    except Exception as e:
        logger.error(f"MIME detection error for {filename}: {e}")
        return False, "Could not verify file content type"
    
    return True, ""


@router.post("/projects/{project_id}/files", response_model=FileResponse)
@limiter.limit("20/minute")  # Stricter limit for uploads
async def upload_file(request: Request, project_id: str, file: UploadFile = File(...)):
    project = await udb.projects_find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    content_bytes = await file.read()
    
    # STEP 2: Upload Security Hardening
    is_valid, error_msg = validate_file_upload(file.filename, content_bytes)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    UPLOAD_DIR = os.path.join("uploads")
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1].lower()
    save_filename = f"{file_id}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, save_filename)
    
    # Guardar archivo fisico
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    # Solo intentar decodificar texto para archivos legibles (PDF, TXT, etc)
    text_content = ""
    if ext in ["txt", "csv", "json", "md"]:
        try:
            text_content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = content_bytes.decode("latin-1", errors="ignore")
    elif ext == "pdf":
        # Placeholder for PDF text extraction if needed during upload
        text_content = f"[Archivo PDF: {file.filename}]"
    else:
        text_content = f"[Archivo Binario {ext.upper()}: {file.filename}]"

    doc = {
        "id": file_id,
        "project_id": project_id,
        "filename": file.filename,
        "file_size": len(content_bytes),
        "file_path": file_path, # Guardamos la ruta real
        "content_text": text_content,
        "status": "pending",
        "category_edge": None,
        "measure_edge": None,
        "doc_type": "plano" if ext in ["dwg", "dxf"] else None,
        "confidence": None,
        "watts": None,
        "lumens": None,
        "tipo_equipo": None,
        "marca": None,
        "modelo": None,
        "areas": None,
        "specialized_data": None,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    await udb.files_insert_one(doc)
    doc.pop("content_text", None)
    return FileResponse(**doc)

@router.get("/projects/{project_id}/files", response_model=List[FileResponse])
async def list_files(project_id: str):
    files = await udb.files_find({"project_id": project_id}, {"content_text": 0})
    return [FileResponse(**f) for f in files]

@router.put("/files/{file_id}", response_model=FileResponse)
async def update_file(file_id: str, update_data: FileUpdate):
    file = await udb.files_find_one({"id": file_id})
    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Preparamos los datos para actualizar, forzando confianza a 1.0 si es edicion manual
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["confidence"] = 1.0
    
    await udb.files_update_one({"id": file_id}, {"$set": update_dict})
    
    updated_file = await udb.files_find_one({"id": file_id})
    return FileResponse(**updated_file)

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    result = await udb.files_delete_one({"id": file_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {"message": "Archivo eliminado"}
