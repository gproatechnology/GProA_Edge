import uuid
from datetime import datetime, timezone, timedelta
from app.db.database import udb

async def seed_demo_data():
    """Seed the database with initial demo projects if empty."""
    projects = await udb.projects_find()
    if len(projects) > 0:
        return 

    print(">>> Seeding rich demo dataset...")
    
    # --- PROYECTO 1: INDUSTRIAL (Existente) ---
    p1_id = str(uuid.uuid4())
    await udb.projects_insert_one({
        "id": p1_id,
        "name": "CCU PV 03 Tristone (DEMO)",
        "typology": "Industrial",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        "priority": "Alta",
        "efficiency": 28.5,
        "file_count": 2,
        "processed_count": 2
    })
    
    # --- PROYECTO 2: RESIDENCIAL ---
    p2_id = str(uuid.uuid4())
    await udb.projects_insert_one({
        "id": p2_id,
        "name": "Torre Mistral - Vivienda Sustentable",
        "typology": "Residencial",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "priority": "Crítica",
        "efficiency": 32.1,
        "file_count": 3,
        "processed_count": 1
    })

    # --- PROYECTO 3: CORPORATIVO ---
    p3_id = str(uuid.uuid4())
    await udb.projects_insert_one({
        "id": p3_id,
        "name": "Reforma 180 Business Center",
        "typology": "Corporativo",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "priority": "Baja",
        "efficiency": 45.0,
        "file_count": 1,
        "processed_count": 1
    })

    # --- ARCHIVOS MOCK ---
    
    # Archivo para P1 (Industrial)
    await udb.files_insert_one({
        "id": str(uuid.uuid4()),
        "project_id": p1_id,
        "filename": "Ficha_Tecnica_LED_Philips.pdf",
        "file_size": 1024,
        "status": "processed",
        "category_edge": "ENERGY",
        "measure_edge": "EEM22",
        "doc_type": "ficha_tecnica",
        "watts": 12.0,
        "lumens": 1100.0,
        "tipo_equipo": "luminaria LED",
        "marca": "Philips",
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    })

    # Archivo para P2 (Residencial - Ahorro Agua)
    await udb.files_insert_one({
        "id": str(uuid.uuid4()),
        "project_id": p2_id,
        "filename": "Griferia_Helvex_BajoConsumo.pdf",
        "file_size": 2048,
        "status": "processed",
        "category_edge": "WATER",
        "measure_edge": "WEM01",
        "doc_type": "ficha_tecnica",
        "tipo_equipo": "Grifo Lavabo",
        "marca": "Helvex",
        "specialized_data": {"caudal_lpm": 1.9, "cumple_edge": True},
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    })

    # Archivo para P3 (Corporativo - HVAC)
    await udb.files_insert_one({
        "id": str(uuid.uuid4()),
        "project_id": p3_id,
        "filename": "Sistema_VRV_Daikin_N4.pdf",
        "file_size": 4096,
        "status": "processed",
        "category_edge": "ENERGY",
        "measure_edge": "EEM09",
        "doc_type": "ficha_tecnica",
        "tipo_equipo": "Aire Acondicionado VRV",
        "marca": "Daikin",
        "specialized_data": {"COP": 4.2, "EER": 14.5},
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    })

    print(">>> Rich demo dataset seeded successfully")
