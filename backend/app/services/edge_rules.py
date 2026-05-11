# EDGE Rules Engine - WBS (Work Breakdown Structure) + Document Inventory
# Defines required documents and calculations per EDGE measure

EDGE_WBS = {
    # ═══════════════ ENERGY ═══════════════
    "EEM01": {
        "categoria": "ENERGY",
        "nombre": "Reduccion de Energia en Envolvente",
        "descripcion": "Ventanas y muros con especificaciones termicas",
        "documentos_requeridos": ["plano", "ficha_tecnica", "memoria"],
        "calculo": "transmitancia_termica",
        "campos_extraccion": ["valor_u", "shgc", "area_vidrio", "area_muro"],
    },
    "EEM02": {
        "categoria": "ENERGY",
        "nombre": "Aislamiento de Techos",
        "descripcion": "Especificaciones de aislamiento termico en techos",
        "documentos_requeridos": ["ficha_tecnica", "memoria"],
        "calculo": "resistencia_termica",
        "campos_extraccion": ["valor_r", "espesor", "material"],
    },
    "EEM03": {
        "categoria": "ENERGY",
        "nombre": "Vidrios de Alto Rendimiento",
        "descripcion": "Vidrios con factor solar y transmitancia controlada",
        "documentos_requeridos": ["ficha_tecnica", "plano"],
        "calculo": "factor_solar",
        "campos_extraccion": ["shgc", "valor_u", "tipo_vidrio"],
    },
    "EEM05": {
        "categoria": "ENERGY",
        "nombre": "Proteccion Solar Externa",
        "descripcion": "Dispositivos de sombra y proteccion solar",
        "documentos_requeridos": ["plano", "ficha_tecnica", "fotografia"],
        "calculo": "factor_sombra",
        "campos_extraccion": ["tipo_proteccion", "angulo", "orientacion"],
    },
    "EEM06": {
        "categoria": "ENERGY",
        "nombre": "Reflectancia de Techos",
        "descripcion": "Techos con alta reflectancia solar (cool roofs)",
        "documentos_requeridos": ["ficha_tecnica", "fotografia"],
        "calculo": "reflectancia_solar",
        "campos_extraccion": ["sri", "reflectancia", "emisividad"],
    },
    "EEM08": {
        "categoria": "ENERGY",
        "nombre": "Ventilacion Natural",
        "descripcion": "Sistemas de ventilacion natural cruzada",
        "documentos_requeridos": ["plano", "memoria"],
        "calculo": "area_ventilacion",
        "campos_extraccion": ["area_ventana", "area_piso", "ratio_ventilacion"],
    },
    "EEM09": {
        "categoria": "ENERGY",
        "nombre": "Aire Acondicionado Eficiente",
        "descripcion": "Sistemas HVAC de alta eficiencia",
        "documentos_requeridos": ["ficha_tecnica", "memoria", "factura"],
        "calculo": "eficiencia_hvac",
        "campos_extraccion": ["cop", "eer", "seer", "capacidad_btu", "refrigerante"],
    },
    "EEM13": {
        "categoria": "ENERGY",
        "nombre": "Sistema de Gestion de Energia",
        "descripcion": "BMS o sistemas de control energetico",
        "documentos_requeridos": ["ficha_tecnica", "memoria"],
        "calculo": None,
        "campos_extraccion": ["tipo_sistema", "marca", "protocolo"],
    },
    "EEM16": {
        "categoria": "ENERGY",
        "nombre": "Energia Renovable",
        "descripcion": "Paneles solares, eolica u otras fuentes renovables",
        "documentos_requeridos": ["ficha_tecnica", "plano", "memoria", "factura"],
        "calculo": "generacion_renovable",
        "campos_extraccion": ["capacidad_kw", "tipo_panel", "eficiencia_panel", "area_paneles"],
    },
    "EEM22": {
        "categoria": "ENERGY",
        "nombre": "Iluminacion Eficiente",
        "descripcion": "Sistema de iluminacion con alta eficacia luminosa",
        "documentos_requeridos": ["plano", "ficha_tecnica", "fotografia"],
        "calculo": "eficacia_luminosa",
        "campos_extraccion": ["watts", "lumens", "tipo_equipo", "cantidad", "eficiencia", "modelo"],
    },
    "EEM23": {
        "categoria": "ENERGY",
        "nombre": "Iluminacion Exterior Eficiente",
        "descripcion": "Iluminacion exterior con alta eficacia",
        "documentos_requeridos": ["plano", "ficha_tecnica"],
        "calculo": "eficacia_luminosa",
        "campos_extraccion": ["watts", "lumens", "tipo_equipo", "cantidad"],
    },

    # ═══════════════ DESIGN & ARCHITECTURE ═══════════════
    "DESIGN": {
        "categoria": "DESIGN",
        "nombre": "Desglose de Áreas y Cargas",
        "descripcion": "Planos arquitectónicos y breakdown de áreas del proyecto",
        "documentos_requeridos": ["plano", "memoria"],
        "calculo": "area_total",
        "campos_extraccion": ["area_m2", "espacios", "niveles"],
    },

    # ═══════════════ WATER ═══════════════
    "WEM01": {
        "categoria": "WATER",
        "nombre": "Griferias de Bajo Flujo",
        "descripcion": "Griferias y duchas con flujo reducido",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": "ahorro_agua",
        "campos_extraccion": ["flujo_lpm", "tipo_griferia", "marca"],
    },
    "WEM02": {
        "categoria": "WATER",
        "nombre": "Sanitarios de Doble Descarga",
        "descripcion": "Inodoros con doble descarga o bajo consumo",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": "consumo_descarga",
        "campos_extraccion": ["litros_descarga_completa", "litros_media_descarga", "marca"],
    },
    "WEM04": {
        "categoria": "WATER",
        "nombre": "Riego Eficiente",
        "descripcion": "Sistemas de riego por goteo o eficiente",
        "documentos_requeridos": ["plano", "ficha_tecnica", "memoria"],
        "calculo": "eficiencia_riego",
        "campos_extraccion": ["tipo_riego", "area_riego", "consumo_estimado"],
    },
    "WEM07": {
        "categoria": "WATER",
        "nombre": "Reuso de Aguas Grises",
        "descripcion": "Tratamiento y reuso de aguas grises",
        "documentos_requeridos": ["plano", "ficha_tecnica", "memoria"],
        "calculo": "volumen_reuso",
        "campos_extraccion": ["capacidad_tratamiento", "tipo_sistema", "volumen_diario"],
    },
    "WEM08": {
        "categoria": "WATER",
        "nombre": "Recoleccion de Agua Lluvia",
        "descripcion": "Sistema de captacion y almacenamiento pluvial",
        "documentos_requeridos": ["plano", "memoria", "ficha_tecnica"],
        "calculo": "captacion_pluvial",
        "campos_extraccion": ["area_captacion", "volumen_cisterna", "precipitacion_anual"],
    },

    # ═══════════════ MATERIALS ═══════════════
    "MEM01": {
        "categoria": "MATERIALS",
        "nombre": "Piso con Contenido Reciclado",
        "descripcion": "Pisos fabricados con material reciclado",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": None,
        "campos_extraccion": ["porcentaje_reciclado", "tipo_material", "area"],
    },
    "MEM02": {
        "categoria": "MATERIALS",
        "nombre": "Estructura con Contenido Reciclado",
        "descripcion": "Acero o concreto con contenido reciclado",
        "documentos_requeridos": ["ficha_tecnica", "factura", "memoria"],
        "calculo": None,
        "campos_extraccion": ["porcentaje_reciclado", "tipo_material", "volumen"],
    },
    "MEM03": {
        "categoria": "MATERIALS",
        "nombre": "Aislamiento con Contenido Reciclado",
        "descripcion": "Aislamiento termico con material reciclado",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": None,
        "campos_extraccion": ["porcentaje_reciclado", "tipo_material", "espesor"],
    },
    "MEM04": {
        "categoria": "MATERIALS",
        "nombre": "Fachada con Contenido Reciclado",
        "descripcion": "Material de fachada con contenido reciclado",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": None,
        "campos_extraccion": ["porcentaje_reciclado", "tipo_material", "area"],
    },
    "MEM05": {
        "categoria": "MATERIALS",
        "nombre": "Madera Certificada para Estructura",
        "descripcion": "Madera con certificacion FSC o similar",
        "documentos_requeridos": ["ficha_tecnica", "factura", "fotografia"],
        "calculo": None,
        "campos_extraccion": ["certificacion", "tipo_madera", "volumen"],
    },
    "MEM06": {
        "categoria": "MATERIALS",
        "nombre": "Madera Certificada para Pisos",
        "descripcion": "Pisos de madera con certificacion",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": None,
        "campos_extraccion": ["certificacion", "tipo_madera", "area"],
    },
    "MEM07": {
        "categoria": "MATERIALS",
        "nombre": "Pintura de Bajo VOC",
        "descripcion": "Pinturas con baja emision de compuestos organicos volatiles",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": None,
        "campos_extraccion": ["nivel_voc", "tipo_pintura", "marca"],
    },
    "MEM08": {
        "categoria": "MATERIALS",
        "nombre": "Selladores de Bajo VOC",
        "descripcion": "Selladores y adhesivos con baja emision VOC",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": None,
        "campos_extraccion": ["nivel_voc", "tipo_producto", "marca"],
    },
    "MEM09": {
        "categoria": "MATERIALS",
        "nombre": "Cielo Raso con Contenido Reciclado",
        "descripcion": "Cielo raso fabricado con material reciclado",
        "documentos_requeridos": ["ficha_tecnica", "factura"],
        "calculo": None,
        "campos_extraccion": ["porcentaje_reciclado", "tipo_material", "area"],
    },
    "MEM10": {
        "categoria": "MATERIALS",
        "nombre": "Prevencion de Residuos de Construccion",
        "descripcion": "Plan de gestion de residuos en obra",
        "documentos_requeridos": ["memoria", "fotografia"],
        "calculo": None,
        "campos_extraccion": ["porcentaje_desvio", "plan_gestion"],
    },

    # ═══════════════ DESIGN ═══════════════
    "DESIGN": {
        "categoria": "DESIGN",
        "nombre": "Diseño General / Áreas",
        "descripcion": "Planos arquitectónicos, áreas y diseño general del proyecto",
        "documentos_requeridos": ["plano"], # Solo plano obligatorio para empezar
        "calculo": "calculo_areas",
        "campos_extraccion": ["area_total", "area_por_espacio", "numero_pisos"],
    },
}


def get_rule(measure: str) -> dict:
    return EDGE_WBS.get(measure, None)


def get_all_rules() -> dict:
    return EDGE_WBS


def get_measures_by_category(category: str) -> dict:
    return {k: v for k, v in EDGE_WBS.items() if v["categoria"] == category}


def validate_project_wbs(files: list) -> dict:
    """Deterministic WBS validation: cross-reference files vs requirements."""
    # Group files by measure
    files_by_measure = {}
    for f in files:
        measure = f.get("measure_edge")
        if not measure:
            continue
        if measure not in files_by_measure:
            files_by_measure[measure] = {"doc_types": set(), "files": []}
        doc_type = f.get("doc_type", "otro")
        files_by_measure[measure]["doc_types"].add(doc_type)
        files_by_measure[measure]["files"].append(f)

    validation = {}
    # Validate each detected measure
    for measure, data in files_by_measure.items():
        rule = get_rule(measure)
        if not rule:
            validation[measure] = {
                "categoria": "UNKNOWN",
                "nombre": measure,
                "estado": "sin_regla",
                "documentos_requeridos": [],
                "documentos_disponibles": list(data["doc_types"]),
                "faltantes": [],
                "progreso": 1.0,
            }
            continue

        required = set(rule["documentos_requeridos"])
        available = data["doc_types"]
        missing = required - available
        progress = len(required & available) / len(required) if required else 1.0

        validation[measure] = {
            "categoria": rule["categoria"],
            "nombre": rule["nombre"],
            "estado": "completo" if not missing else "incompleto",
            "documentos_requeridos": list(required),
            "documentos_disponibles": list(available),
            "faltantes": list(missing),
            "progreso": round(progress, 2),
            "calculo": rule.get("calculo"),
            "num_archivos": len(data["files"]),
        }

    return validation


def get_project_coverage(files: list) -> dict:
    """Calculate overall EDGE project coverage across all categories."""
    detected_measures = set()
    for f in files:
        m = f.get("measure_edge")
        if m:
            detected_measures.add(m)

    total_measures = len(EDGE_WBS)
    detected = len(detected_measures)

    categories_coverage = {}
    for cat in ["ENERGY", "WATER", "MATERIALS", "DESIGN"]:
        cat_measures = {k for k, v in EDGE_WBS.items() if v["categoria"] == cat}
        cat_detected = cat_measures & detected_measures
        categories_coverage[cat] = {
            "total": len(cat_measures),
            "detected": len(cat_detected),
            "measures": sorted(list(cat_detected)),
            "missing": sorted(list(cat_measures - cat_detected)),
        }

    return {
        "total_measures": total_measures,
        "detected_measures": detected,
        "coverage_percent": round((detected / total_measures) * 100, 1) if total_measures else 0,
        "categories": categories_coverage,
    }
