from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime, timezone
from app.db.database import udb
from app.core.config import DEMO_MODE

router = APIRouter()


def _require_debug_mode():
    """Bloquea endpoints de debug si DEBUG no está activo."""
    if not DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail="Debug endpoints are disabled when DEMO_MODE is false."
        )


@router.post("/seed")
async def seed_data():
    _require_debug_mode()
    # ------------------------------------------------------------
    # 1. PROYECTOS (10 proyectos variados)
    # ------------------------------------------------------------
    projects = [
        {
            "id": "p1-mock",
            "name": "Centro Comercial Plaza Norte",
            "typology": "Retail",
            "square_meters": 12500,
            "annual_consumption_kwh": 875000,
            "priority": "Alta",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 4,
            "processed_count": 3,
        },
        {
            "id": "p2-mock",
            "name": "Hotel Mar Azul",
            "typology": "Hotel",
            "square_meters": 8500,
            "annual_consumption_kwh": 620000,
            "priority": "Media",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 3,
            "processed_count": 2,
        },
        {
            "id": "p3-mock",
            "name": "Planta Industrial Norte",
            "typology": "Industrial",
            "square_meters": 35000,
            "annual_consumption_kwh": 2500000,
            "priority": "Crítica",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 6,
            "processed_count": 4,
        },
        {
            "id": "p4-mock",
            "name": "Hospital Universitario",
            "typology": "Healthcare",
            "square_meters": 42000,
            "annual_consumption_kwh": 3800000,
            "priority": "Crítica",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 5,
            "processed_count": 5,
        },
        {
            "id": "p5-mock",
            "name": "Edificio Administrativo Sur",
            "typology": "Office",
            "square_meters": 18000,
            "annual_consumption_kwh": 1120000,
            "priority": "Media",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 3,
            "processed_count": 1,
        },
        {
            "id": "p6-mock",
            "name": "Supermercado Los Andes",
            "typology": "Retail",
            "square_meters": 5200,
            "annual_consumption_kwh": 650000,
            "priority": "Alta",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 2,
            "processed_count": 2,
        },
        {
            "id": "p7-mock",
            "name": "Data Center GProA",
            "typology": "Data Center",
            "square_meters": 6000,
            "annual_consumption_kwh": 1500000,
            "priority": "Crítica",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 4,
            "processed_count": 3,
        },
        {
            "id": "p8-mock",
            "name": "Escuela Técnica Industrial",
            "typology": "Education",
            "square_meters": 9500,
            "annual_consumption_kwh": 380000,
            "priority": "Baja",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 2,
            "processed_count": 0,
        },
        {
            "id": "p9-mock",
            "name": "Aeropuerto Regional",
            "typology": "Transport",
            "square_meters": 28000,
            "annual_consumption_kwh": 2950000,
            "priority": "Alta",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 7,
            "processed_count": 6,
        },
        {
            "id": "p10-mock",
            "name": "Centro de Distribución Logístico",
            "typology": "Logistics",
            "square_meters": 45000,
            "annual_consumption_kwh": 1850000,
            "priority": "Media",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 5,
            "processed_count": 3,
        }
    ]

    # Insertar proyectos (sin duplicados)
    for p in projects:
        existing = await udb.projects_find_one({"id": p["id"]})
        if not existing:
            await udb.projects_insert_one(p)

    # ------------------------------------------------------------
    # 2. ARCHIVOS (más de 30 archivos, con variedad de tipos y estados)
    # ------------------------------------------------------------
    files = [
        # Proyecto Retail - Centro Comercial
        {
            "id": "f1-mock", "project_id": "p1-mock", "filename": "plano_iluminacion_pasillos.pdf", "file_size": 1250000,
            "status": "processed", "category_edge": "Lighting", "measure_edge": "LED Retrofit", "doc_type": "Blueprints",
            "confidence": 0.96, "watts": 28.0, "lumens": 3200.0, "tipo_equipo": "Panel LED", "marca": "Philips", "modelo": "CoreLine Slim",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f2-mock", "project_id": "p1-mock", "filename": "inventario_lamparas_actual.xlsx", "file_size": 89000,
            "status": "processed", "category_edge": "Inventory", "doc_type": "Spreadsheet",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f3-mock", "project_id": "p1-mock", "filename": "factura_electrica_ene_mar.pdf", "file_size": 320000,
            "status": "processed", "category_edge": "Utility Bill", "doc_type": "Invoice", "confidence": 0.92,
            "consumption_kwh": 218750, "cost": 32812.5,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f4-mock", "project_id": "p1-mock", "filename": "esquema_subestacion.pdf", "file_size": 2100000,
            "status": "pending", "doc_type": "Electrical Diagram",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Hotel
        {
            "id": "f5-mock", "project_id": "p2-mock", "filename": "consumo_energetico_hotel_2024.xlsx", "file_size": 150000,
            "status": "processed", "category_edge": "Utility Bill", "doc_type": "Spreadsheet", "confidence": 0.95,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f6-mock", "project_id": "p2-mock", "filename": "certificado_eficiencia_energetica.pdf", "file_size": 450000,
            "status": "processed", "category_edge": "Efficiency Certificate", "confidence": 0.88,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f7-mock", "project_id": "p2-mock", "filename": "foto_termica_habitaciones.jpg", "file_size": 2850000,
            "status": "pending", "category_edge": "Thermal Imaging",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Industrial
        {
            "id": "f8-mock", "project_id": "p3-mock", "filename": "diagrama_unifilar_linea_produccion.pdf", "file_size": 3450000,
            "status": "processed", "category_edge": "Electrical Diagram", "doc_type": "Single Line", "confidence": 0.97,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f9-mock", "project_id": "p3-mock", "filename": "medicion_potencia_motores.xlsx", "file_size": 230000,
            "status": "processed", "category_edge": "Measurement", "doc_type": "Spreadsheet", "confidence": 0.99,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f10-mock", "project_id": "p3-mock", "filename": "planta_industrial_completa.dwg", "file_size": 8900000,
            "status": "pending", "category_edge": "CAD", "doc_type": "Drawing",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f11-mock", "project_id": "p3-mock", "filename": "analisis_carga_transformadores.pdf", "file_size": 1870000,
            "status": "processed", "category_edge": "Analysis", "confidence": 0.91,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Hospital
        {
            "id": "f12-mock", "project_id": "p4-mock", "filename": "especificacion_equipos_medicos.pdf", "file_size": 5200000,
            "status": "processed", "category_edge": "Medical Equipment", "confidence": 0.94,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f13-mock", "project_id": "p4-mock", "filename": "consumo_grupos_electrogenos.xlsx", "file_size": 98000,
            "status": "processed", "category_edge": "Generator", "confidence": 0.96,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f14-mock", "project_id": "p4-mock", "filename": "auditoria_iluminacion_quirófanos.pdf", "file_size": 2100000,
            "status": "processed", "category_edge": "Lighting", "measure_edge": "LED Upgrade", "doc_type": "Audit",
            "confidence": 0.98, "watts": 120.0, "lumens": 15000.0,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Oficina
        {
            "id": "f15-mock", "project_id": "p5-mock", "filename": "plan_ahorro_energía_2025.docx", "file_size": 450000,
            "status": "pending", "doc_type": "Report",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f16-mock", "project_id": "p5-mock", "filename": "facturas_agosto_diciembre.pdf", "file_size": 1250000,
            "status": "processed", "category_edge": "Utility Bill", "confidence": 0.89,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Supermercado
        {
            "id": "f17-mock", "project_id": "p6-mock", "filename": "layout_camaras_frigorificas.pdf", "file_size": 980000,
            "status": "processed", "category_edge": "Refrigeration", "confidence": 0.93,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f18-mock", "project_id": "p6-mock", "filename": "historial_mantenimiento_equipos.xlsx", "file_size": 167000,
            "status": "processed", "category_edge": "Maintenance", "confidence": 0.90,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Data Center
        {
            "id": "f19-mock", "project_id": "p7-mock", "filename": "PUE_metricas_trimestrales.csv", "file_size": 45000,
            "status": "processed", "category_edge": "Efficiency Metric", "doc_type": "CSV", "confidence": 1.0,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f20-mock", "project_id": "p7-mock", "filename": "especificacion_ups.pdf", "file_size": 2870000,
            "status": "processed", "category_edge": "UPS", "confidence": 0.97,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f21-mock", "project_id": "p7-mock", "filename": "cooling_diagram.png", "file_size": 3450000,
            "status": "pending", "category_edge": "Cooling System",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Escuela
        {
            "id": "f22-mock", "project_id": "p8-mock", "filename": "consumo_aulas_laboratorios.xlsx", "file_size": 89000,
            "status": "pending", "category_edge": "Consumption Data",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f23-mock", "project_id": "p8-mock", "filename": "plan_de_iluminacion_led.pdf", "file_size": 1100000,
            "status": "pending", "category_edge": "Lighting",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Aeropuerto
        {
            "id": "f24-mock", "project_id": "p9-mock", "filename": "normativa_eficiencia_aeropuertos.pdf", "file_size": 3250000,
            "status": "processed", "category_edge": "Regulation", "confidence": 0.87,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f25-mock", "project_id": "p9-mock", "filename": "inventario_equipos_planta.csv", "file_size": 123000,
            "status": "processed", "category_edge": "Inventory", "confidence": 0.95,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f26-mock", "project_id": "p9-mock", "filename": "analisis_iluminacion_pistas.pdf", "file_size": 4520000,
            "status": "pending", "category_edge": "Lighting",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f27-mock", "project_id": "p9-mock", "filename": "huella_carbono_operaciones.xlsx", "file_size": 98000,
            "status": "processed", "category_edge": "Carbon Footprint", "confidence": 0.92,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        # Logística
        {
            "id": "f28-mock", "project_id": "p10-mock", "filename": "layout_almacen_automatizado.pdf", "file_size": 2120000,
            "status": "processed", "category_edge": "Warehouse", "confidence": 0.96,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f29-mock", "project_id": "p10-mock", "filename": "consumo_flota_electrica.xlsx", "file_size": 156000,
            "status": "pending", "category_edge": "Fleet",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f30-mock", "project_id": "p10-mock", "filename": "simulacion_ahorro_energetico.pdf", "file_size": 3450000,
            "status": "processed", "category_edge": "Simulation", "confidence": 0.98,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "f31-mock", "project_id": "p10-mock", "filename": "ordenes_mantenimiento_2024.xlsx", "file_size": 233000,
            "status": "processed", "category_edge": "Maintenance", "confidence": 0.94,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    for f in files:
        existing = await udb.files_find_one({"id": f["id"]})
        if not existing:
            await udb.files_insert_one(f)

    return {
        "message": "Mock data seeded successfully (extended version)",
        "projects_added": len(projects),
        "files_added": len(files)
    }


@router.post("/clear")
async def clear_data():
    _require_debug_mode()
    if udb.mode == "sqlite":
        await udb._ensure_sqlite()
        await udb.conn.execute("DELETE FROM projects")
        await udb.conn.execute("DELETE FROM files")
        await udb.conn.commit()
    else:
        from app.db.database import db
        await db.projects.delete_many({})
        await db.files.delete_many({})
    return {"message": "All data cleared"}