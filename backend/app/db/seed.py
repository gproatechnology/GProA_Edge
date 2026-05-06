import uuid
from datetime import datetime, timezone
from app.db.database import udb

async def seed_demo_data():
    """Seed the database with initial demo projects if empty."""
    projects = await udb.projects_find()
    if len(projects) > 0:
        return # Already has data

    print(">>> Seeding demo project...")
    project_id = str(uuid.uuid4())
    
    # 1. Create Project
    await udb.projects_insert_one({
        "id": project_id,
        "name": "CCU PV 03 Tristone (DEMO)",
        "typology": "Industrial - Light Industry",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "priority": "Alta",
        "efficiency": 25,
        "file_count": 2,
        "processed_count": 2
    })

    # 2. Add sample files (already processed)
    await udb.files_insert_one({
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "filename": "Ficha_Tecnica_LED_Philips.pdf",
        "file_size": 102400,
        "status": "processed",
        "category_edge": "ENERGY",
        "measure_edge": "EEM22",
        "doc_type": "ficha_tecnica",
        "confidence": 0.98,
        "watts": 12.0,
        "lumens": 1100.0,
        "tipo_equipo": "luminaria LED",
        "marca": "Philips",
        "specialized_data": {
            "total_lumens": 1100.0,
            "total_watts": 12.0,
            "eficacia_global": 91.67,
            "cumple_edge": True,
            "luminarias": [
                {"id": "L1", "modelo": "CoreLine", "cantidad": 1, "lumens": 1100, "watts": 12, "eficiencia": 91.67}
            ]
        },
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    })

    await udb.files_insert_one({
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "filename": "Plano_Arquitectonico_N1.pdf",
        "file_size": 204800,
        "status": "processed",
        "category_edge": "DESIGN",
        "measure_edge": "DESIGN",
        "doc_type": "plano",
        "confidence": 0.90,
        "areas": [
            {"nombre": "Producción", "area_m2": 1200.5},
            {"nombre": "Oficinas", "area_m2": 150.0},
            {"nombre": "Almacén", "area_m2": 450.0}
        ],
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    })

    print(">>> Demo project seeded successfully")
