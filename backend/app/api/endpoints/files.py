from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
from datetime import datetime, timezone
from app.db.database import udb
from app.schemas.schemas import FileResponse, FileUpdate

router = APIRouter()

@router.post("/projects/{project_id}/files", response_model=FileResponse)
async def upload_file(project_id: str, file: UploadFile = File(...)):
    project = await udb.projects_find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    import os
    UPLOAD_DIR = os.path.join("uploads")
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    file_id = str(uuid.uuid4())
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ""
    save_filename = f"{file_id}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, save_filename)

    content_bytes = await file.read()
    
    # Guardar archivo fisico
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    # Solo intentar decodificar texto para archivos legibles (PDF, TXT, etc)
    text_content = ""
    if ext in ["txt", "csv", "json", "md"]:
        try:
            text_content = content_bytes.decode("utf-8")
        except:
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
