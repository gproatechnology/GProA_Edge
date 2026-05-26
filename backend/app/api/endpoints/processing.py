from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid
import asyncio
from datetime import datetime, timezone
import logging
from app.db.database import udb
from app.services.ai_service import processing_jobs, process_single_file_pipeline
from app.services.audit_service import AuditService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/projects/{project_id}/pipeline")
async def run_pipeline(project_id: str):
    """Run the full deterministic pipeline for EDGE processing."""
    from app.services.pipeline import ProcessingPipeline
    
    files = await udb.files_find({"project_id": project_id})
    if not files:
        raise HTTPException(status_code=404, detail="No files found for project")
    
    file_list = [{"path": f.get("path", ""), "type": f.get("type", "dxf")} for f in files]
    
    pipeline = ProcessingPipeline(project_id=project_id, revision="v1")
    result = await pipeline.run(file_list)
    
    return result


@router.get("/projects/{project_id}/artifacts")
async def list_artifacts(project_id: str):
    """List persisted artifacts for a project."""
    from app.services.pipeline.artifacts import artifact_store
    return {"project_id": project_id, "artifacts": artifact_store.list_artifacts(project_id)}

async def _run_batch_processing(job_id: str, files: list):
    job = processing_jobs[job_id]
    
    # Procesar hasta 5 archivos de manera concurrente para no saturar CPU/Memoria ni los rate limits de Gemini
    semaphore = asyncio.Semaphore(5)
    job["processed"] = 0
    
    async def process_file(i, f):
        async with semaphore:
            try:
                job["current_file"] = f.get("filename", "unknown")
                job["current_step"] = f"Procesando concurrentemente: {f.get('filename', 'unknown')}"
                logger.info(f"[{job_id}] Starting file {i+1}/{len(files)}: {f.get('filename')}")
                
                # Timeout de 300s para PDFs grandes (hasta 7MB). El parser analiza texto, tablas, áreas y geometría completa
                result = await asyncio.wait_for(
                    process_single_file_pipeline(f, job_id),
                    timeout=300.0
                )
                logger.info(f"[{job_id}] Completed file {i+1}/{len(files)}: {f.get('filename')}")
            except asyncio.TimeoutError:
                logger.error(f"[{job_id}] Timeout processing file {f.get('filename')}")
                await udb.files_update_one({"id": f.get("id")}, {"$set": {"status": "error", "error_msg": "Timeout"}})
            except Exception as e:
                logger.error(f"[{job_id}] Error processing file {f.get('filename')}: {e}")
                await udb.files_update_one({"id": f.get("id")}, {"$set": {"status": "error", "error_msg": str(e)}})
            finally:
                job["processed"] += 1

    # Lanzar todas las tareas de procesamiento
    tasks = [process_file(i, f) for i, f in enumerate(files)]
    await asyncio.gather(*tasks)
    
    job["status"] = "completed"
    job["current_step"] = "Completado"
    job["current_file"] = ""
    job["completed_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(f"[{job_id}] Batch completed")


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

    semaphore = asyncio.Semaphore(5)
    async def _process_with_semaphore(f):
        async with semaphore:
            return await process_single_file_pipeline(f)

    tasks = [_process_with_semaphore(f) for f in files]
    results = await asyncio.gather(*tasks)
    
    return {"processed": len(results), "results": results}


@router.post("/files/{file_id}/process")
async def process_single_file(file_id: str):
    f = await udb.files_find_one({"id": file_id})
    if not f:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    result = await process_single_file_pipeline(f)
    return result


_CONCURRENCY_LIMIT = 10


@router.post("/processing/batch")
async def process_batch(project_id: str, background_tasks: BackgroundTasks):
    files = await udb.files_find({"project_id": project_id, "status": "pending"})
    if not files:
        return {"processed": 0, "message": "No pending files"}

    semaphore = asyncio.Semaphore(_CONCURRENCY_LIMIT)

    async def _schedule(file_id: str):
        async with semaphore:
            try:
                await AuditService.process_file(file_id)
            except Exception as exc:
                logger.error(f"File {file_id} failed: {exc}")

    def _dispatch():
        asyncio.run(asyncio.gather(*[_schedule(f["id"]) for f in files]))

    background_tasks.add_task(_dispatch)
    return {"processed": len(files), "status": "scheduled", "concurrency": _CONCURRENCY_LIMIT}
