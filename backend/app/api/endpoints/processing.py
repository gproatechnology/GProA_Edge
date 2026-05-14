from fastapi import APIRouter, HTTPException
import uuid
import asyncio
from datetime import datetime, timezone
import logging
from app.db.database import udb
from app.services.ai_service import processing_jobs, process_single_file_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)

async def _run_batch_processing(job_id: str, files: list):
    job = processing_jobs[job_id]
    try:
        for i, f in enumerate(files):
            job["current_file"] = f["filename"]
            job["current_step"] = f"Clasificando ({i+1}/{len(files)})"
            job["processed"] = i

            result = await process_single_file_pipeline(f, job_id)
            job["results"].append(result)

        job["status"] = "completed"
        job["processed"] = len(files)
        job["current_step"] = "Completado"
        job["current_file"] = ""
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        job["status"] = "error"
        job["current_step"] = f"Error: {str(e)}"


@router.post("/projects/{project_id}/process-edge")
async def process_edge_project(project_id: str):
    from app.core.config import gemini_client
    project = await udb.projects_find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    files = await udb.files_find({"project_id": project_id})
    if not files:
        raise HTTPException(status_code=400, detail="No hay archivos en el proyecto")

    job_id = str(uuid.uuid4())
    
    # --- MODO DEMO INSTANTÁNEO ---
    if not gemini_client:
        logger.info(f"MODO DEMO: Procesando {len(files)} archivos instantáneamente.")
        results = []
        for f in files:
            res = await process_single_file_pipeline(f, job_id)
            results.append(res)
        
        # ACTUALIZAR MÉTRICAS DEL PROYECTO TRAS PROCESAMIENTO
        try:
            from app.services.edge_rules import validate_project_wbs, get_project_coverage
            all_files = await udb.files_find({"project_id": project_id})
            processed_files = [f for f in all_files if f.get("status") == "processed"]
            if processed_files:
                validate_project_wbs(processed_files)
                coverage = get_project_coverage(processed_files)
                await udb.projects_update_one({"id": project_id}, {"$set": {
                    "efficiency": coverage["coverage_percent"],
                    "processed_count": len(processed_files)
                }})
                logger.info(f"Métricas actualizadas para proyecto {project_id}: {coverage['coverage_percent']}%")
        except Exception as e:
            logger.error(f"Error actualizando métricas en modo demo: {e}")

        # Registrar el job como completado
        processing_jobs[job_id] = {
            "project_id": project_id,
            "status": "completed",
            "total": len(files),
            "processed": len(files),
            "current_file": "",
            "current_step": "Completado (Demo)",
            "results": results,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        return {
            "job_id": job_id, 
            "total_files": len(files), 
            "status": "completed", 
            "message": "Procesamiento demo completado instantáneamente",
            "results": results
        }
    # -----------------------------

    # Actualizar métricas iniciales (para archivos ya procesados antes de esta ejecución)
    from app.services.edge_rules import validate_project_wbs, get_project_coverage
    processed_files = [f for f in files if f.get("status") == "processed"]
    if processed_files:
        validate_project_wbs(processed_files)
        coverage = get_project_coverage(processed_files)
        await udb.projects_update_one({"id": project_id}, {"$set": {
            "efficiency": coverage["coverage_percent"],
            "processed_count": len(processed_files)
        }})

    processing_jobs[job_id] = {
        "project_id": project_id,
        "status": "running",
        "total": len(files),
        "processed": 0,
        "current_file": "",
        "current_step": "Iniciando...",
        "results": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    asyncio.create_task(_run_batch_processing(job_id, files))
    return {"job_id": job_id, "total_files": len(files), "status": "running"}


@router.get("/projects/{project_id}/process-status/{job_id}")
async def get_process_status(project_id: str, job_id: str):
    job = processing_jobs.get(job_id)
    
    if not job:
        # Fallback para Modo Demo o reinicios: si no existe el job pero los archivos están procesados
        processed_count = await udb.files_count_documents({"project_id": project_id, "status": "processed"})
        total_count = await udb.files_count_documents({"project_id": project_id})
        
        if total_count > 0 and processed_count == total_count:
            return {
                "job_id": job_id,
                "status": "completed",
                "total": total_count,
                "processed": processed_count,
                "percent": 100,
                "current_file": "",
                "current_step": "Completado (Rescatado de DB)",
                "results": [],
            }
        
        raise HTTPException(status_code=404, detail="Job no encontrado")
        
    return {
        "job_id": job_id,
        "status": job["status"],
        "total": job["total"],
        "processed": job["processed"],
        "percent": round((job["processed"] / job["total"]) * 100) if job["total"] > 0 else 0,
        "current_file": job["current_file"],
        "current_step": job["current_step"],
        "results": job.get("results", []),
    }


@router.post("/projects/{project_id}/process")
async def process_project_files(project_id: str):
    files = await udb.files_find({"project_id": project_id, "status": "pending"})
    if not files:
        raise HTTPException(status_code=400, detail="No hay archivos pendientes de procesar")

    results = []
    for f in files:
        result = await process_single_file_pipeline(f)
        results.append(result)
    return {"processed": len(results), "results": results}


@router.post("/files/{file_id}/process")
async def process_single_file(file_id: str):
    f = await udb.files_find_one({"id": file_id})
    if not f:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    result = await process_single_file_pipeline(f)
    return result
