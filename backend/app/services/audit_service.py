import logging
import json
import os
from datetime import datetime
from app.db.database import udb
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.cad_parser import CADParser
from app.services.edge_processors import run_specialized_processor

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    async def process_file(file_id: str, api_key: str = None):
        """Orchestrate the full audit flow for a single file."""
        file_record = await udb.files_find_one({"id": file_id})
        if not file_record:
            logger.error(f"File not found: {file_id}")
            return None

        project_id = file_record["project_id"]
        file_path = file_record.get("file_path")
        filename = file_record["filename"]

        if not file_path or not os.path.exists(file_path):
            logger.error(f"File path invalid or missing: {file_path}")
            # Actualizar status a error
            await udb.files_update_one(
                {"id": file_id}, 
                {"$set": {"status": "error", "error_message": "File not found"}}
            )
            return None

        # 1. Classification (Detect Measure)
        measure = AuditService.detect_measure(filename)
        logger.info(f"Auditing file {filename} as measure {measure}")

        # Actualizar status a processing
        await udb.files_update_one(
            {"id": file_id},
            {"$set": {"status": "processing", "measure_edge": measure}}
        )

        # 2. Parsing (Extract raw content)
        content = ""
        ext = filename.split(".")[-1].lower()
        
        import asyncio
        try:
            if ext == "pdf":
                def _run_pdf_parser():
                    parser = PDFParser()
                    return parser.parse(file_path)
                pdf_data = await asyncio.to_thread(_run_pdf_parser)
                content = json.dumps(pdf_data)
            elif ext in ["dxf", "dwg"]:
                def _run_cad_parser():
                    parser = CADParser(file_path)
                    return parser.extract_all()
                cad_data = await asyncio.to_thread(_run_cad_parser)
                content = json.dumps(cad_data)
            else:
                logger.warning(f"No specialized parser for extension {ext}")
                content = f"Raw content of {filename}"
        except Exception as e:
            logger.error(f"Parsing error for {filename}: {e}")
            return None

        # 3. Specialized Processing (AI Analysis)
        audit_result = await run_specialized_processor(measure, content, api_key)
        
        # 4. Update Database
        if audit_result:
            update_data = {
                "status": "processed",
                "measure_edge": measure,
                "specialized_data": audit_result
            }
            # Extract common metrics if available
            if "total_watts" in audit_result:
                update_data["watts"] = audit_result["total_watts"]
            if "total_lumens" in audit_result:
                update_data["lumens"] = audit_result["total_lumens"]
            
            await udb.files_update_one({"id": file_id}, {"$set": update_data})
            
            # 5. Update Project Summary
            await AuditService.recalculate_project_metrics(project_id)
            
            return audit_result
        return None

    @staticmethod
    def detect_measure(filename: str) -> str:
        """Heuristic to detect EDGE measure from filename."""
        fn = filename.upper()
        if "EEM22" in fn or "LUM" in fn or "LIGHT" in fn or "EL1" in fn or "EL2" in fn or "EL3" in fn or "EL7" in fn or "EL" in fn: return "EEM22"
        if "EEM01" in fn or "WWR" in fn or "WINDOW" in fn: return "EEM01"
        if "EEM09" in fn or "HVAC" in fn or "AIRE" in fn: return "EEM09"
        if "WEM01" in fn or "GRIF" in fn or "SHOWER" in fn: return "WEM01"
        if "WEM02" in fn or "WC" in fn or "TOILET" in fn: return "WEM02"
        if "EEM16" in fn or "SOLAR" in fn or "RENEW" in fn: return "EEM16"
        return "GENERAL"

    @staticmethod
    async def recalculate_project_metrics(project_id: str):
        """Aggregate metrics from all processed files to update project dashboard."""
        files = await udb.files_find({"project_id": project_id, "status": "processed"})
        
        total_co2 = 0.0
        total_savings = 0.0
        count = 0
        
        for f in files:
            data = f.get("specialized_data", {})
            # Mock calculation: each processed EEM file contributes to CO2 reduction
            if f.get("measure_edge", "").startswith("EEM"):
                total_co2 += 1.5 # Generic multiplier for demo
                total_savings += data.get("energy_savings", 5.0)
                count += 1
        
        await udb.projects_update_one(
            {"id": project_id},
            {"$set": {
                "processed_count": len(files),
                "co2_reduction": round(total_co2, 2),
                "efficiency": round(total_savings / count if count > 0 else 0, 1)
            }}
        )

audit_service = AuditService()
