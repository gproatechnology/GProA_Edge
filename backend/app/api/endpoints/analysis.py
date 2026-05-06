from fastapi import APIRouter
from app.db.database import udb
from app.services.edge_rules import validate_project_wbs, get_project_coverage

router = APIRouter()

@router.get("/projects/{project_id}/wbs-validation")
async def get_wbs_validation(project_id: str):
    files = await udb.files_find(
        {"project_id": project_id, "status": "processed"},
        {"content_text": 0}
    )

    validation = validate_project_wbs(files)
    coverage = get_project_coverage(files)

    return {
        "measures": validation,
        "coverage": coverage,
        "total_files": await udb.files_count_documents({"project_id": project_id}),
        "processed_files": len(files),
    }

@router.get("/projects/{project_id}/kpis")
async def get_project_kpis(project_id: str):
    files = await udb.files_find(
        {"project_id": project_id, "status": "processed"},
        {"content_text": 0}
    )

    kpis = {}

    lighting_files = [f for f in files if f.get("measure_edge") in ("EEM22", "EEM23") and f.get("specialized_data")]
    if lighting_files:
        total_lm = 0
        total_w = 0
        all_luminaires = []
        alertas = []
        for f in lighting_files:
            sd = f["specialized_data"]
            total_lm += sd.get("total_lumens", 0)
            total_w += sd.get("total_watts", 0)
            all_luminaires.extend(sd.get("luminarias", []))
            alertas.extend(sd.get("alertas", []))

        eficacia = round(total_lm / total_w, 2) if total_w > 0 else 0
        kpis["EEM22"] = {
            "nombre": "Eficacia Luminosa Global",
            "valor": eficacia,
            "unidad": "lm/W",
            "umbral_edge": 90,
            "cumple": eficacia >= 90,
            "total_lumens": total_lm,
            "total_watts": total_w,
            "num_luminarias": len(all_luminaires),
            "alertas": list(set(alertas)),
        }

    hvac_files = [f for f in files if f.get("measure_edge") == "EEM09" and f.get("specialized_data")]
    if hvac_files:
        cops = []
        for f in hvac_files:
            sd = f["specialized_data"]
            for eq in sd.get("equipos", []):
                if eq.get("cop"):
                    cops.append(eq["cop"])
        avg_cop = round(sum(cops) / len(cops), 2) if cops else 0
        kpis["EEM09"] = {
            "nombre": "COP Promedio HVAC",
            "valor": avg_cop,
            "unidad": "COP",
            "umbral_edge": 3.0,
            "cumple": avg_cop >= 3.0,
            "num_equipos": sum(len(f["specialized_data"].get("equipos", [])) for f in hvac_files),
        }

    water_files = [f for f in files if f.get("measure_edge") in ("WEM01", "WEM02") and f.get("specialized_data")]
    if water_files:
        for f in water_files:
            measure = f["measure_edge"]
            sd = f["specialized_data"]
            if measure not in kpis:
                kpis[measure] = {
                    "nombre": "Flujo Promedio" if measure == "WEM01" else "Descarga Promedio",
                    "valor": sd.get("flujo_promedio", 0),
                    "unidad": "lpm" if measure == "WEM01" else "lpd",
                    "num_aparatos": len(sd.get("aparatos", [])),
                }

    return kpis

@router.get("/projects/{project_id}/extracted-data")
async def get_extracted_data(project_id: str):
    files = await udb.files_find(
        {"project_id": project_id, "status": "processed"},
        {"content_text": 0}
    )
    return files

@router.get("/projects/{project_id}/edge-status")
async def get_edge_status(project_id: str):
    files = await udb.files_find(
        {"project_id": project_id, "status": "processed"},
        {"content_text": 0}
    )

    categories = {}
    measures = {}
    for f in files:
        cat = f.get("category_edge", "UNKNOWN")
        meas = f.get("measure_edge", "UNKNOWN")
        categories[cat] = categories.get(cat, 0) + 1
        measures[meas] = measures.get(meas, 0) + 1

    validation = validate_project_wbs(files)
    faltantes = [
        {"medida": k, "faltan": v["faltantes"]}
        for k, v in validation.items()
        if v["estado"] == "incompleto"
    ]

    # Calculate Estimated Savings based on KPIs
    kpis = await get_project_kpis(project_id)
    savings = {
        "energy": 0,
        "water": 0,
        "materials": 0
    }
    
    # Energy savings estimation (based on Lighting efficiency)
    if "EEM22" in kpis:
        val = kpis["EEM22"]["valor"]
        if val >= 90: savings["energy"] = 35
        elif val >= 60: savings["energy"] = 20
        else: savings["energy"] = 5

    # Water savings estimation
    if "WEM01" in kpis:
        val = kpis["WEM01"]["valor"]
        if val <= 6: savings["water"] = 40
        elif val <= 9: savings["water"] = 25
        else: savings["water"] = 10
    
    # Default materials (until we have M-WBS)
    if "MATERIALS" in categories:
        savings["materials"] = min(categories["MATERIALS"] * 10, 30)

    total = await udb.files_count_documents({"project_id": project_id})
    processed = await udb.files_count_documents({"project_id": project_id, "status": "processed"})

    return {
        "categories": categories,
        "measures": measures,
        "savings": savings,
        "faltantes": faltantes,
        "total_files": total,
        "processed_files": processed,
        "wbs_validation": validation,
    }
