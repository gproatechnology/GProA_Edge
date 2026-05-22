# EDGE Specialized Processors - Measure-specific analysis
# Each processor runs analysis tailored to the EDGE measure detected
# Supports demo mode: if api_key is None, returns mock data

import json
import uuid
import logging
import os
import re
from abc import abstractmethod
from google.genai import types
from app.core.config import gemini_client, GEMINI_API_KEY
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

logger = logging.getLogger(__name__)


# ── ESQUEMAS PYDANTIC (Strict Structured Outputs) ──────────────────────

class LuminariaItem(BaseModel):
    id: str = Field(description="Identificador o número de la luminaria (ej. L-01, Type A)")
    modelo: str = Field(description="Modelo, referencia o descripción de la luminaria")
    cantidad: int = Field(description="Cantidad total de unidades de este modelo")
    lumens: float = Field(description="Lúmenes por unidad (LM)")
    watts: float = Field(description="Watts por unidad (W). Si incluye balasto, sumar su potencia.")
    notas: Optional[str] = Field(None, description="Notas importantes como: dimerizable, con balasto, duplicada, etc.")

class EEM22ResponseSchema(BaseModel):
    luminarias: List[LuminariaItem] = Field(description="Lista de todas las luminarias encontradas en el documento")
    alertas: List[str] = Field(description="Alertas detectadas (ej. luminarias duplicadas, falta de datos, etc.)")
    luminarias_emergencia: int = Field(description="Cantidad de luminarias de emergencia detectadas (deben excluirse si no aportan a la iluminación general)")
    total_luminarias: int = Field(description="Suma total de la cantidad de luminarias")


# ── MOCK PROCESSORS (Demo Mode) ────────────────────────────────────────

def process_eem22_luminaires_mock(content: str) -> dict:
    """Return empty data if analysis fails."""
    return {
        "luminarias": [],
        "total_watts": 0,
        "total_lumens": 0,
        "mensaje": "No se encontraron luminarias detalladas en el documento."
    }

def process_eem09_hvac_mock(content: str) -> dict:
    """Return mock EEM09 data for demo."""
    return {
        "equipos": [
            {"id": "HVAC-1", "tipo": "Split", "marca": "Daikin", "modelo": "FTXS35", "capacidad_btu": 12000, "cop": 3.8, "eer": 13.0, "seer": 16.0, "refrigerante": "R-410A"},
            {"id": "HVAC-2", "tipo": "VRF", "marca": "Toshiba", "modelo": "MMY-AP0480", "capacidad_btu": 48000, "cop": 4.2, "eer": 14.5, "seer": 18.0, "refrigerante": "R-32"},
        ],
        "cop_promedio": 4.0,
        "alertas": [],
    }

def process_eem16_renewables_mock(content: str) -> dict:
    """Return mock EEM16 data for demo."""
    return {
        "tipo_sistema": "fotovoltaico",
        "capacidad_instalada_kw": 15.5,
        "paneles": [
            {"marca": "SunPower", "modelo": "E19-310", "watts_pico": 310, "cantidad": 50, "eficiencia": 0.22}
        ],
        "generacion_anual_estimada_kwh": 18000,
        "area_total_paneles_m2": 65.0,
        "inversor": "SMA Sunny Tripower 15000",
        "alertas": [],
    }

def process_water_fixtures_mock(measure: str, content: str) -> dict:
    """Return mock water fixture data for demo."""
    if measure == "WEM01":
        return {
            "aparatos": [
                {"tipo": "grifo", "marca": "Grohe", "modelo": "Eurosmart", "flujo_lpm": 6.0, "cantidad": 8},
                {"tipo": "ducha", "marca": "Grohe", "modelo": "SmartWater", "flujo_lpm": 9.5, "cantidad": 4},
            ],
            "flujo_promedio": 7.2,
            "alertas": [],
        }
    else:  # WEM02
        return {
            "aparatos": [
                {"tipo": "inodoro", "marca": "Toto", "modelo": "Cisterna", "flujo_lpm": 4.8, "cantidad": 6},
                {"tipo": "urinario", "marca": "Geberit", "modelo": "Sigma", "flujo_lpm": 1.0, "cantidad": 3},
            ],
            "flujo_promedio": 3.4,
            "alertas": [],
        }


# ── REAL PROCESSORS ────────────────────────────────────────────────────

async def process_eem22_luminaires(content: str, api_key: str) -> dict:
    """EEM22 Specialized: Extract luminaire table using strict Pydantic Schemas and calculate global efficacy."""
    if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
        return process_eem22_luminaires_mock(content)

    prompt = """Analiza este documento de iluminación y extrae TODAS las luminarias encontradas en las tablas o especificaciones técnicas.
    
    Asegúrate de mapear correctamente cada columna: identificador, modelo, cantidad, lúmenes y watts unitarios."""

    try:
        config = types.GenerateContentConfig(
            system_instruction=(
                "Eres un ingeniero especialista en iluminación analizando tablas de luminarias para la certificación EDGE EEM22. "
                "Tu objetivo es realizar una extracción limpia y estructurada."
            ),
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=EEM22ResponseSchema,
        )

        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, content],
            config=config
        )
        
        data = json.loads(response.text.strip())

        # ── Cálculos Deterministas Post-Extracción ──
        luminarias = data.get("luminarias", [])
        total_lumens_weighted = 0
        total_watts_weighted = 0
        total_qty_calculated = 0

        for lum in luminarias:
            qty = lum.get("cantidad", 1) or 1
            lumens = lum.get("lumens", 0.0) or 0.0
            watts = lum.get("watts", 0.0) or 0.0
            
            total_lumens_weighted += lumens * qty
            total_watts_weighted += watts * qty
            total_qty_calculated += qty
            
            if watts > 0:
                lum["eficiencia"] = round(lumens / watts, 2)
            else:
                lum["eficiencia"] = 0.0

        eficacia_global = round(total_lumens_weighted / total_watts_weighted, 2) if total_watts_weighted > 0 else 0

        data["eficacia_global"] = eficacia_global
        data["total_lumens"] = total_lumens_weighted
        data["total_watts"] = total_watts_weighted
        data["total_luminarias"] = total_qty_calculated
        data["cumple_edge"] = eficacia_global >= 90.0

        return data

    except Exception as e:
        logger.error(f"EEM22 processor error: {e}")
        return process_eem22_luminaires_mock(content)


# ── CONSTANTS ───────────────────────────────────────────────────────────
MAX_CHARS = 5000
DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


# ── UNIFILAR DIAGRAM PROCESSOR ───────────────────────────────────────────

async def process_unifilar_diagram(pdf_bytes: bytes, api_key: str) -> dict:
    """Process PDF unifilar diagrams asynchronously with retry logic."""
    if not api_key or not api_key.strip():
        return {"error": "API Key requerida para analisis Unifilar", "total_watts": 0}

    prompt = """Analiza este DIAGRAMA UNIFILAR / CUADRO DE CARGAS y extrae los Tableros de Alumbrado (Lighting Panels).

REGLAS OBLIGATORIAS:
1. Busca cadenas literales exactas como "MIEL PANEL ROWIND", "TAB-AN1", "TG-1", "EL100", "EL200", "EL300"
2. SI NO existe un cuadro de cargas numerico explícito en el plano (tabla con valores de Watts o kVA), debes forzar total_watts = 0
3. Si esta en kVA, convierte a Watts multiplicando por 1000

Para CADA tablero de alumbrado extrae:
- nombre: nombre del tablero (ej. TAB-AN1, TG-1)
- descripcion: que alimenta (alumbrado, fuerza, etc.)
- watts: carga total conectada en Watts

Responde SOLO en JSON:
{
  "tipo_documento": "diagrama_unifilar",
  "tableros": [
    {
      "nombre": "string",
      "descripcion": "string",
      "watts": 0
    }
  ],
  "total_watts": 0,
  "mensaje": "Resumen de carga extraido del diagrama unifilar."
}"""

    config = types.GenerateContentConfig(
        system_instruction="Eres un experto en ingenieria electrica. Tu objetivo es extraer el resumen de cargas de alumbrado de diagramas unifilares. Responde SOLO JSON. Si no hay cuadro de cargas numerico explicito, total_watts debe ser 0.",
        temperature=0.1,
        response_mime_type="application/json"
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = await gemini_client.aio.models.generate_content(
                model=DEFAULT_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(text=prompt),
                            types.Part(inline_data={"mime_type": "application/pdf", "data": pdf_bytes})
                        ]
                    )
                ],
                config=config
            )
            data = json.loads(response.text.strip())
            if not data.get("total_watts") and data.get("tableros"):
                data["total_watts"] = sum(t.get("watts", 0) for t in data["tableros"])
            return data
        except Exception as e:
            error_msg = str(e)
            is_retryable = any(kw in error_msg for kw in ["quota", "rate", "timeout", "network", "500", "503"])
            if is_retryable and attempt < MAX_RETRIES - 1:
                import asyncio
                await asyncio.sleep(RETRY_DELAYS[attempt])
                continue
            logger.error(f"Unifilar processor error: {error_msg}")
            return {"error": error_msg, "total_watts": 0}


# ── HVAC PROCESSOR ─────────────────────────────────────────────────────

async def process_eem09_hvac(content: str, api_key: str) -> dict:
    """EEM09 Specialized: Extract HVAC equipment data."""
    if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
        return process_eem09_hvac_mock(content)

    prompt = f"""Analiza este documento de equipos HVAC y extrae la informacion de cada equipo.

Para CADA equipo extrae:
- id: identificador
- tipo: tipo de equipo (split, VRF, chiller, etc.)
- marca: fabricante
- modelo: referencia
- capacidad_btu: capacidad en BTU/h
- cop: coeficiente de rendimiento
- eer: ratio de eficiencia energetica
- seer: ratio estacional (si aplica)
- refrigerante: tipo de refrigerante

Responde SOLO en JSON:
{{
  "equipos": [
    {{
      "id": "string",
      "tipo": "string",
      "marca": "string",
      "modelo": "string",
      "capacidad_btu": 0,
      "cop": 0.0,
      "eer": 0.0,
      "seer": 0.0,
      "refrigerante": "string"
    }}
  ],
  "cop_promedio": 0.0,
  "alertas": []
}}

Contenido:
{content[:4000]}"""

    try:
        config = types.GenerateContentConfig(
            system_instruction="Eres un ingeniero mecanico analizando equipos HVAC para certificacion EDGE. Responde SOLO en JSON valido.",
            temperature=0.3,
            response_mime_type="application/json"
        )
        response = await gemini_client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=config
        )
        result_text = response.text.strip()

        return json.loads(result_text)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"EEM09 processor error: {e}")
        return process_eem09_hvac_mock(content)


# ── RENEWABLES PROCESSOR ───────────────────────────────────────────────

async def process_eem16_renewables(content: str, api_key: str) -> dict:
    """EEM16 Specialized: Extract renewable energy data."""
    if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
        return process_eem16_renewables_mock(content)

    prompt = f"""Analiza este documento de sistema de energia renovable y extrae:

- tipo_sistema: fotovoltaico, eolico, etc.
- capacidad_instalada_kw: capacidad total
- paneles: lista de paneles con marca, modelo, watts_pico, cantidad
- generacion_anual_estimada_kwh: si esta disponible
- area_total_paneles_m2: area total de paneles
- inversor: marca y modelo del inversor

Responde SOLO en JSON:
{{
  "tipo_sistema": "string",
  "capacidad_instalada_kw": 0,
  "paneles": [{{
    "marca": "string",
    "modelo": "string",
    "watts_pico": 0,
    "cantidad": 0,
    "eficiencia": 0.0
  }}],
  "generacion_anual_estimada_kwh": 0,
  "area_total_paneles_m2": 0,
  "inversor": "string",
  "alertas": []
}}

Contenido:
{content[:4000]}"""

    try:
        config = types.GenerateContentConfig(
            system_instruction="Eres un ingeniero de energias renovables analizando sistemas fotovoltaicos. Responde SOLO en JSON valido.",
            temperature=0.3,
            response_mime_type="application/json"
        )
        response = await gemini_client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=config
        )
        result_text = response.text.strip()

        return json.loads(result_text)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"EEM16 processor error: {e}")
        return process_eem16_renewables_mock(content)


# ── WATER FIXTURES PROCESSOR ───────────────────────────────────────────

EDGE_BASELINES = {
    "WATER": {
        "Faucets": 6.0,       # LPM (Litros por minuto)
        "Showers": 10.0,     # LPM
        "Toilets": 6.0,      # LPF (Litros por descarga)
        "Urinals": 1.0,      # LPF
        "KitchenFaucets": 6.0 # LPM
    }
}

async def process_water_fixtures(content: str, measure: str, api_key: str) -> dict:
    """WEM01/WEM02 Specialized: Extract water fixture data and calculate savings."""
    if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
        data = process_water_fixtures_mock(measure, content)
    else:
        prompt = f"""Analiza este documento de aparatos sanitarios/griferias para medida EDGE {measure}.
    
    Extrae para cada aparato:
    - tipo: grifo, ducha, inodoro, urinario, etc.
    - marca
    - modelo
    - flujo_lpm: flujo en litros por minuto (griferias) o litros por descarga (sanitarios)
    - cantidad
    
    Responde SOLO en JSON:
    {{
      "aparatos": [
        {{
          "tipo": "string",
          "marca": "string",
          "modelo": "string",
          "flujo_lpm": 0.0,
          "cantidad": 0
        }}
      ]
    }}
    
    Contenido:
    {content[:4000]}"""

        try:
            config = types.GenerateContentConfig(
                system_instruction="Eres un ingeniero hidraulico analizando griferias y sanitarios para EDGE. Responde SOLO en JSON valido.",
                temperature=0.3,
                response_mime_type="application/json"
            )
            response = await gemini_client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            result_text = response.text.strip()
            data = json.loads(result_text)
        except Exception as e:
            logger.error(f"Water processor error: {e}")
            data = process_water_fixtures_mock(measure, content)

    # ── Real Calculation vs Baseline ───────────────────────────────────
    aparatos = data.get("aparatos", [])
    total_flow = 0
    total_qty = 0
    savings_detail = []

    for item in aparatos:
        qty = item.get("cantidad", 1) or 1
        flow = item.get("flujo_lpm", 0.0) or 0.0
        tipo = item.get("tipo", "").lower()
        
        # Determine baseline
        baseline = 6.0 # Default
        if "ducha" in tipo or "shower" in tipo: baseline = EDGE_BASELINES["WATER"]["Showers"]
        elif "inodoro" in tipo or "toilet" in tipo or "sanitario" in tipo: baseline = EDGE_BASELINES["WATER"]["Toilets"]
        elif "urinario" in tipo or "urinal" in tipo: baseline = EDGE_BASELINES["WATER"]["Urinals"]
        elif "cocina" in tipo or "kitchen" in tipo: baseline = EDGE_BASELINES["WATER"]["KitchenFaucets"]
        else: baseline = EDGE_BASELINES["WATER"]["Faucets"]

        saving = ((baseline - flow) / baseline) * 100 if baseline > 0 else 0
        
        item["baseline"] = baseline
        item["saving_percent"] = round(saving, 1)
        
        total_flow += flow * qty
        total_qty += qty
        savings_detail.append(saving)

    data["flujo_promedio"] = round(total_flow / total_qty, 2) if total_qty > 0 else 0
    data["ahorro_global_estimado"] = round(sum(savings_detail) / len(savings_detail), 1) if savings_detail else 0
    data["cumple_edge"] = data["ahorro_global_estimado"] >= 20 # EDGE requires 20% savings
    
    return data


# ── A700 / A250 — LAYER-FILTER HELPERS ───────────────────────────────────────

_A700_WHITELIST: frozenset[str] = frozenset({
    "DOOR", "PUERTA", "A700", "ENVELOPE", "EXTERIOR",
    "WALL", "MURO", "FACHADA",
})

_A250_WHITELIST: frozenset[str] = frozenset({
    "STAIR", "ESCALERA", "A250", "CIRCULATION",
    "STAIRS", "ESC", "VERTICAL",
})

_DOOR_BLOCK_KEYWORDS: tuple[str, ...] = (
    "DOOR", "PUERTA", "GATE", "PORTON", "COURTYARD",
    "EMERG", "EMERGENCY", "FIRE",
)


def _layer_in_whitelist(layer_name: str, whitelist: frozenset[str]) -> bool:
    """True si la capa está en la whitelist (comparación case-insensitive)."""
    return layer_name.upper().strip() in whitelist


def _extract_dxf_layers(doc: "ezdxf.document.Drawing") -> set[str]:
    """Devuelve el conjunto de nombres de capa definidos en el DXF."""
    return {layer.dxf.name for layer in doc.layers}


def _iter_relevant_inserts(msp, whitelist: frozenset[str], keywords: tuple[str, ...]) -> list[dict]:
    """Recorre bloques INSERT filtrando por capa y por palabra clave en el nombre del bloque."""
    results: list[dict] = []
    for blk in msp.query("INSERT"):
        layer = blk.dxf.get("layer", "")
        if not _layer_in_whitelist(layer, whitelist):
            continue
        block_name = blk.dxf.get("name", "").upper()
        if not any(kw in block_name for kw in keywords):
            continue

        # Atributos del bloque (texto embebido)
        attrs: dict[str, str] = {}
        try:
            for attrib in blk.attribs:
                tag = attrib.dxf.get("tag", "")
                value = attrib.dxf.get("text", "")
                if tag:
                    attrs[tag.upper()] = value
        except Exception:
            pass

        insert_pt = blk.dxf.get("insert", (0, 0, 0))
        results.append({
            "block_name": block_name,
            "layer": layer,
            "insert_x": round(float(insert_pt[0]), 3),
            "insert_y": round(float(insert_pt[1]), 3),
            "scale_x": round(float(blk.dxf.get("xscale", 1.0) or 1.0), 3),
            "scale_y": round(float(blk.dxf.get("yscale", 1.0) or 1.0), 3),
            "attributes": attrs,
        })
    return results


def _iter_relevant_polylines(msp, whitelist: frozenset[str]) -> list[dict]:
    """Recorre LWPOLYLINE filtrando por capa, calcula área y bounding box."""
    results: list[dict] = []
    for poly in msp.query("LWPOLYLINE"):
        layer = poly.dxf.get("layer", "")
        if not _layer_in_whitelist(layer, whitelist):
            continue

        try:
            flags = poly.dxf.get("flags", 0) if hasattr(poly.dxf, "flags") else 0
            is_closed = bool(flags & 1)
            pts = list(poly.get_points())

            # Heurística de cierre: menos de 10 uds de separación entre extremos
            if not is_closed and len(pts) > 2:
                p1, p2 = pts[0], pts[-1]
                dist = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5
                if dist < 10.0:
                    is_closed = True

            area = poly.area() if is_closed else None
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            results.append({
                "layer": layer,
                "is_closed": is_closed,
                "area_dxf_units": round(area, 3) if area is not None else None,
                "vertex_count": len(pts),
                "bbox_min_x": round(min(xs), 3) if xs else 0.0,
                "bbox_min_y": round(min(ys), 3) if ys else 0.0,
                "bbox_max_x": round(max(xs), 3) if xs else 0.0,
                "bbox_max_y": round(max(ys), 3) if ys else 0.0,
            })
        except Exception as exc:
            logger.debug("LWPOLYLINE capa '%s': %s", layer, exc)

    return results


# ── A700 — DOOR / ENVELOPE SHEET (DXF) ────────────────────────────────────────

def process_a700_doors(file_path: str) -> dict:
    """
    Procesa un DXF de la hoja A700 (Puertas / Envolvente térmica).

    Estrategia de filtrado en dos pasos:
      1. Whitelist de capas (_A700_WHITELIST): todo lo demás se descarta.
      2. Palabras clave en nombre de bloque INSERT: evita procesar mobiliario.

    Devuelve un dict compatible con EEM_MaterialesPuertasResponse.
    """
    import ezdxf

    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        all_layers = _extract_dxf_layers(doc)
    except Exception as exc:
        return {"error": f"No se pudo abrir el DXF A700: {exc}"}

    relevant = {l for l in all_layers if _layer_in_whitelist(l, _A700_WHITELIST)}
    if not relevant:
        logger.warning(
            "A700 DXF sin capas reconocidas. Definidas: %s — Esperadas: %s",
            ", ".join(sorted(all_layers)[:10]),
            ", ".join(sorted(_A700_WHITELIST)),
        )
    logger.info("A700 DXF — capas:%d, relevantes:%d", len(all_layers), len(relevant))

    # Bloques INSERT (puertas)
    raw_doors = _iter_relevant_inserts(msp, relevant, _DOOR_BLOCK_KEYWORDS)

    puertas: list[dict] = []
    seen_labels: set[str] = set()
    for door in raw_doors:
        attrs = door["attributes"]
        label = (attrs.get("TAG") or attrs.get("TEXT")
                 or f"P-{door['insert_x']:.0f}-{door['insert_y']:.0f}").strip()
        if label.lower() in seen_labels:
            continue
        seen_labels.add(label.lower())

        bn = door["block_name"].upper()
        door_type = "Peatonal"
        if "VEH" in bn:
            door_type = "Vehicular"
        elif "EMERG" in bn or "FIRE" in bn:
            door_type = "Emergencia"
        elif "CORTINA" in bn or "ROLLING" in bn:
            door_type = "Cortina enrollable"

        width_m  = door["scale_x"]
        height_m = door["scale_y"]
        location = (
            f"Hoja A700, coords "
            f"X={door['insert_x']:.2f}, Y={door['insert_y']:.2f}"
        )

        puertas.append({
            "etiqueta": label,
            "tipo": door_type,
            "ancho_m": width_m,
            "alto_m": height_m,
            "material_hoja": "Acero",
            "vidrio": None,
            "cantidad": 1,
            "ubicacion_sugerida": location,
        })

    # Polilíneas de envolvente
    envolvente = _iter_relevant_polylines(msp, relevant)
    obs: list[str] = []
    for env in envolvente:
        if env["is_closed"] and env["area_dxf_units"]:
            obs.append(
                f"Área envolvente en capa '{env['layer']}': "
                f"{env['area_dxf_units']:.2f} uds CAD "
                "(verificar unidades del plano)."
            )

    logger.info("A700 DXF — puertas:%d, areas_envolvente:%d", len(puertas), len(obs))

    return {
        "proyecto_id": "",
        "fecha_plano": "",
        "lista_puertas": puertas,
        "observaciones_envolvente": obs,
    }


# ── A700 / A250 — Stair Plano Item Schema ─────────────────────────────────────

class StairPlanoItem(BaseModel):
    id_escalera:     str  = Field(description="Identificador de la escalera (ej. E-01, ESC-PPAL)")
    ancho_nar:       float = Field(description="Ancho de la escalera en metros")
    huella_m:        float = Field(description="Huella (tread) en metros")
    contrahuella_m:  float = Field(description="Contrahuella (riser) en metros")
    numero_peldanos: int   = Field(description="Número total de peldaños")
    material:        str   = Field(description="Material de la escalera (ej. Hormigón, Acero, Madera)")
    ubicacion:       str   = Field(description="Ubicación en el edificio (ej. Acceso Principal, Emergencia)")


class A250_StairResponse(BaseModel):
    proyecto_id:           str               = Field(description="Número de proyecto detectado en el Title Block")
    fecha_plano:           str               = Field(description="Fecha del plano")
    status_extraccion:     str               = Field(description="'completo' | 'necesita_vision' | 'error'")
    lista_escaleras:       List[StairPlanoItem] = Field(description="Lista de escaleras extraídas del plano")
    notas_generales:       List[str]         = Field(description="Notas extraídas de las tablas de texto del PDF")
    texto_extraido_raw:    Optional[str]     = Field(None, description="Texto plano completo extraído por PyMuPDF (para debug)")


# ── A250 — STAIR SHEET (PDF) ─────────────────────────────────────────────────

_MIN_CHARS_FOR_PARSED = 50
_STAIR_NOTE_KEYWORDS = ("ESCAL", "PELD", "HUELL", "CONTR", "DESNIV",
                         "TABIQUE", "STAIR", "STEP", "RISER", "TREAD", "LANDING")


def _extract_pdf_text(file_path: str) -> tuple[str, list[str], bool]:
    """
    Extrae texto del PDF con PyMuPDF.

    Returns
    -------
    (all_text, stair_notes, is_scanned)
        all_text    : texto plano completo
        stair_notes : líneas con palabras clave de escalera
        is_scanned  : True si el PDF tiene menos de _MIN_CHARS_FOR_PARSED caracteres
    """
    import fitz
    all_lines: list[str] = []
    stair_notes: list[str] = []

    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            all_lines.append(stripped)
            upper = stripped.upper()
            if any(kw in upper for kw in _STAIR_NOTE_KEYWORDS):
                stair_notes.append(stripped)
    doc.close()

    total_chars = sum(len(l) for l in all_lines)
    is_scanned = total_chars < _MIN_CHARS_FOR_PARSED
    return "\n".join(all_lines), stair_notes, is_scanned


def _build_a250_response(
    *,
    raw_text: str,
    stair_notes: list[str],
    is_scanned: bool,
    project_id: str = "",
    fecha_plano: str = "",
) -> dict:
    """Construye el dict de respuesta A250 a partir de los datos extraídos."""
    obs: list[str] = []
    status = "completo"
    if is_scanned:
        obs.append(
            "PDF A250 detectado como escaneado "
            f"({len(raw_text)} chars); se requiere Gemini Vision."
        )
        status = "necesita_vision"

    obs.extend(f"[Nota A250] {n}" for n in stair_notes[:10])

    return {
        "proyecto_id":      project_id,
        "fecha_plano":      fecha_plano,
        "status_extraccion": status,
        "lista_escaleras":  [],
        "notas_generales":  obs,
        "texto_extraido_raw": raw_text[:500] if raw_text else None,
        "_is_scanned":      is_scanned,
    }


def process_a250_stairs(file_path: str) -> dict:
    """
    Procesa un plano PDF de la hoja A250 (Escaleras / Circulación vertical).

    Flujo:
      1. PyMuPDF extrae todo el texto.
      2. Se filtran las líneas con palabras clave de escalera.
      3. Si el PDF es escaneado, se marca 'necesita_vision' — no se lanza excepción
         ni se interrumpe el pipeline.
      4. El dict devuelto valida contra A250_StairResponse.
    """
    try:
        raw_text, stair_notes, is_scanned = _extract_pdf_text(file_path)
        logger.info(
            "A250 PDF — %d chars | %d notas de escalera | scanned:%s",
            len(raw_text), len(stair_notes), is_scanned,
        )
        return _build_a250_response(
            raw_text=raw_text,
            stair_notes=stair_notes,
            is_scanned=is_scanned,
        )
    except Exception as exc:
        logger.error("Error procesando A250 PDF '%s': %s", file_path, exc)
        return {
            "proyecto_id": "",
            "fecha_plano": "",
            "status_extraccion": "error",
            "lista_escaleras": [],
            "notas_generales": [f"Error de extracción: {exc}"],
            "texto_extraido_raw": None,
            "_is_scanned": False,
        }


# ── GLOBAL DISPATCHER ─────────────────────────────────────────────────────

MEASURE_PROCESSORS = {
    "EEM22": process_eem22_luminaires,
    "EEM23": process_eem22_luminaires,  # Same lighting logic
    "EEM09": process_eem09_hvac,
    "EEM16": process_eem16_renewables,
    "WEM01": process_water_fixtures,
    "WEM02": process_water_fixtures,
    "A700": process_a700_doors,          # Doors / Envelope sheet (DXF)
    "A250": process_a250_stairs,         # Stair / Vertical circulation sheet (PDF)
}


# ── EEM DOOR / ENVELOPE RESPONSE MODELS ────────────────────────────────────

class PuertaPlanoItem(BaseModel):
    etiqueta: str = Field(description="Código identificador en el plano (ej. P-01, PR-02)")
    tipo: str = Field(description="Tipo de puerta (ej. Peatonal, Vehicular, Emergencia, Cortina enrollable)")
    ancho_m: float = Field(description="Ancho de la puerta en metros")
    alto_m: float = Field(description="Alto de la puerta en metros")
    material_hoja: str = Field(description="Material principal de la hoja (ej. Acero, Aluminio, Vidrio, Madera)")
    vidrio: Optional[str] = Field(None, description="Especificación del vidrio si aplica (ej. Claro 6mm, Doble cristal, N/A)")
    cantidad: int = Field(default=1, description="Cantidad de puertas de este tipo identificadas")
    ubicacion_sugerida: str = Field(description="Ubicación según plano (ej. Acceso Principal, Salida de Emergencia, Almacén)")


class EEM_MaterialesPuertasResponse(BaseModel):
    proyecto_id: str = Field(description="Número de proyecto detectado en el cuadro de datos (Title Block)")
    fecha_plano: str = Field(description="Fecha del plano encontrada en el cuadro de datos")
    lista_puertas: List[PuertaPlanoItem] = Field(description="Listado estructurado de todas las puertas encontradas en el Door Schedule")
    observaciones_envolvente: List[str] = Field(description="Notas sobre puentes térmicos, sellado perimetral o infiltración de aire encontradas en las notas generales.")



async def run_specialized_processor(
    measure: str,
    content: str,
    api_key: str = None,
    filename: str = "",
    pdf_bytes: bytes | None = None,
) -> dict:
    """Run the specialized processor for a given measure, if available."""
    
    # Check for Unifilar keywords in content OR filename
    text_to_check = (content + " " + filename).upper()
    unifilar_keywords = ["UNIFILAR", "DIAGRAMA UNIFILAR", "SINGLE LINE", "CUADRO DE CARGAS", "EL100", "EL200", "EL300"]
    
    if any(kw in text_to_check for kw in unifilar_keywords):
        logger.info(f"Unifilar pattern detected in {filename}. Routing to specialized Unifilar processor.")
        return await process_unifilar_diagram(pdf_bytes or b"", api_key)

    processor = MEASURE_PROCESSORS.get(measure)
    if processor:
        import inspect
        sig = inspect.signature(processor)
        if "measure" in sig.parameters:
            return await processor(content, measure, api_key)
        return await processor(content, api_key)
    return None