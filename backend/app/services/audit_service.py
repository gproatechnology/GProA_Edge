import logging
import json
import os
import asyncio
from pathlib import Path
from datetime import datetime
from app.db.database import udb
from app.services.pipeline.pipeline import ProcessingPipeline
from app.services.edge_rules import detect_measure

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    async def process_file(file_id: str, api_key: str = None):
        """
        Regulatory-grade audit flow using the ProcessingPipeline.
        Implements GPT Point 11: Unified classification, extraction, and compliance.
        """
        file_record = await udb.files_find_one({"id": file_id})
        if not file_record:
            logger.error(f"File not found: {file_id}")
            return None

        project_id = file_record["project_id"]
        file_path = file_record.get("file_path")
        filename = file_record["filename"]

        if not file_path or not os.path.exists(file_path):
            logger.error(f"File path invalid or missing: {file_path}")
            await udb.files_update_one(
                {"id": file_id}, 
                {"$set": {"status": "error", "error_message": "File not found"}}
            )
            return None

        # 1. Classification (Regulatory-Grade Detection)
        measure = detect_measure(filename)
        logger.info(f"🚀 Audit Pipeline: Starting analysis for {filename} (Measure: {measure})")

        await udb.files_update_one(
            {"id": file_id},
            {"$set": {"status": "processing", "measure_edge": measure}}
        )

        # 2. Orchestration via Engineering Compiler (Pipeline)
        # We wrap the file in the format expected by the pipeline
        pipeline_files = [{
            "path": file_path,
            "name": filename,
            "type": filename.split(".")[-1].lower(),
            "measure": measure
        }]

        pipeline = ProcessingPipeline(project_id)
        
        try:
            # The pipeline handles parsing, extraction (v1.0), validation, and memory GC
            pipeline_result = await pipeline.run(pipeline_files)
            
            # 3. Update Database with Consolidated Results
            summary = pipeline_result.get("summary", {})
            
            update_data = {
                "status": "processed",
                "measure_edge": measure,
                "specialized_data": pipeline_result,
                "confidence": summary.get("overall_confidence", 0.0),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Extract metrics from stage results for the dashboard
            for stage_res in pipeline_result.get("stage_results", []):
                if stage_res["stage_name"] == "compliance_scoring":
                    update_data["compliance_score"] = stage_res["output"].get("compliance_score", 0)

            await udb.files_update_one({"id": file_id}, {"$set": update_data})
            
            # 4. Update Project Summary
            await AuditService.recalculate_project_metrics(project_id)
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"❌ Audit Pipeline failed for {filename}: {e}")
            await udb.files_update_one(
                {"id": file_id},
                {"$set": {"status": "error", "error_message": str(e)}}
            )
            return None

    @staticmethod
    async def recalculate_project_metrics(project_id: str):
        """Regulatory-grade project aggregation."""
        files = await udb.files_find({"project_id": project_id, "status": "processed"})
        
        total_compliance = 0.0
        processed_count = 0
        
        for f in files:
            score = f.get("compliance_score", 0.0)
            total_compliance += score
            processed_count += 1
        
        await udb.projects_update_one(
            {"id": project_id},
            {"$set": {
                "processed_count": processed_count,
                "average_compliance": round(total_compliance / processed_count if processed_count > 0 else 0, 2),
                "last_audit_at": datetime.utcnow().isoformat()
            }}
        )

audit_service = AuditService()
