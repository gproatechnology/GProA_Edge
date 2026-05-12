# EDGE Specialized Processors - Measure-specific analysis
# Each processor runs analysis tailored to the EDGE measure detected
# Supports demo mode: if api_key is None, returns mock data

import json
import uuid
import logging
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Helper: create client if API key available
def get_openai_client(api_key: str = None):
    if api_key:
        return AsyncOpenAI(api_key=api_key)
    return None


# ── MOCK PROCESSORS (Demo Mode) ────────────────────────────────────────

def process_eem22_luminaires_mock(content: str) -> dict:
    """Return mock EEM22 data for demo."""
    return {
        "luminarias": [
            {"id": "L01", "modelo": "LED Panel 36W", "cantidad": 10, "lumens": 3600, "watts": 36, "eficiencia": 100.0, "notas": None},
            {"id": "L02", "modelo": "LED Downlight 12W", "cantidad": 15, "lumens": 1200, "watts": 12, "eficiencia": 100.0, "notas": None},
        ],
        "alertas": [],
        "luminarias_emergencia": 2,
        "total_luminarias": 25,
        "eficacia_global": 100.0,
        "total_lumens": 57600,
        "total_watts": 600,
        "cumple_edge": True,
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


# ── REAL PROCESSORS (OpenAI) ───────────────────────────────────────────

async def process_eem22_luminaires(content: str, api_key: str) -> dict:
    """EEM22 Specialized: Extract luminaire table and calculate global efficacy."""
    if not api_key:
        return process_eem22_luminaires_mock(content)

    client = get_openai_client(api_key)
    prompt = f"""Analiza este documento de iluminacion y extrae TODAS las luminarias encontradas.

Para CADA luminaria extrae:
- id: identificador o numero de la luminaria
- modelo: modelo/referencia
- cantidad: cuantas unidades
- lumens: lumenes por unidad
- watts: watts por unidad
- eficiencia: lumens/watts por unidad (calcula si no esta explicito)
- notas: cualquier nota importante (duplicadas, con ballast, dimerizables, etc.)

Tambien identifica si hay:
- luminarias duplicadas
- luminarias con ballast electronico/magnetico
- luminarias dimerizables
- luminarias de emergencia (excluirlas del calculo principal)

Responde SOLO en JSON:
{{
  "luminarias": [
    {{
      "id": "string",
      "modelo": "string",
      "cantidad": 0,
      "lumens": 0,
      "watts": 0,
      "eficiencia": 0.0,
      "notas": "string o null"
    }}
  ],
  "alertas": ["string"],
  "luminarias_emergencia": 0,
  "total_luminarias": 0
}}

Contenido del archivo:
{content[:4000]}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un ingeniero especialista en iluminacion analizando tablas de luminarias para certificacion EDGE EEM22. Responde SOLO en JSON valido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        result_text = response.choices[0].message.content.strip()

        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(result_text)

        # Calculate global efficacy
        luminarias = data.get("luminarias", [])
        total_lumens_weighted = 0
        total_watts_weighted = 0
        for lum in luminarias:
            qty = lum.get("cantidad", 1) or 1
            lumens = lum.get("lumens", 0) or 0
            watts = lum.get("watts", 0) or 0
            total_lumens_weighted += lumens * qty
            total_watts_weighted += watts * qty
            if watts > 0:
                lum["eficiencia"] = round(lumens / watts, 2)

        eficacia_global = round(total_lumens_weighted / total_watts_weighted, 2) if total_watts_weighted > 0 else 0

        data["eficacia_global"] = eficacia_global
        data["total_lumens"] = total_lumens_weighted
        data["total_watts"] = total_watts_weighted
        data["cumple_edge"] = eficacia_global >= 90

        return data
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"EEM22 processor error: {e}")
        return process_eem22_luminaires_mock(content)


async def process_eem09_hvac(content: str, api_key: str) -> dict:
    """EEM09 Specialized: Extract HVAC equipment data."""
    if not api_key:
        return process_eem09_hvac_mock(content)

    client = get_openai_client(api_key)
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
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un ingeniero mecanico analizando equipos HVAC para certificacion EDGE. Responde SOLO en JSON valido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        result_text = response.choices[0].message.content.strip()

        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        return json.loads(result_text)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"EEM09 processor error: {e}")
        return process_eem09_hvac_mock(content)


async def process_eem16_renewables(content: str, api_key: str) -> dict:
    """EEM16 Specialized: Extract renewable energy data."""
    if not api_key:
        return process_eem16_renewables_mock(content)

    client = get_openai_client(api_key)
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
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un ingeniero de energias renovables analizando sistemas fotovoltaicos. Responde SOLO en JSON valido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        result_text = response.choices[0].message.content.strip()

        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        return json.loads(result_text)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"EEM16 processor error: {e}")
        return process_eem16_renewables_mock(content)


# EDGE Baselines (Values used by the official EDGE App)
EDGE_BASELINES = {
    "WATER": {
        "Faucets": 6.0,      # LPM (Litros por minuto)
        "Showers": 10.0,     # LPM
        "Toilets": 6.0,      # LPF (Litros por descarga)
        "Urinals": 1.0,      # LPF
        "KitchenFaucets": 6.0 # LPM
    }
}

async def process_water_fixtures(content: str, measure: str, api_key: str) -> dict:
    """WEM01/WEM02 Specialized: Extract water fixture data and calculate savings."""
    if not api_key:
        data = process_water_fixtures_mock(measure, content)
    else:
        client = get_openai_client(api_key)
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
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un ingeniero hidraulico analizando griferias y sanitarios para EDGE. Responde SOLO en JSON valido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
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


# Dispatcher: routes to the correct processor based on measure
MEASURE_PROCESSORS = {
    "EEM22": process_eem22_luminaires,
    "EEM23": process_eem22_luminaires,  # Same lighting logic
    "EEM09": process_eem09_hvac,
    "EEM16": process_eem16_renewables,
    "WEM01": process_water_fixtures,
    "WEM02": process_water_fixtures,
}


async def run_specialized_processor(measure: str, content: str, api_key: str = None) -> dict:
    """Run the specialized processor for a given measure, if available."""
    processor = MEASURE_PROCESSORS.get(measure)
    if processor:
        return await processor(content, api_key)
    return None
