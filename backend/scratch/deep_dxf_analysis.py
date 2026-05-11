import ezdxf
import os
from collections import Counter

uploads_dir = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads'
# El más reciente de 20MB
path = os.path.join(uploads_dir, '2de1d522-4ddc-4741-99d9-67f216a2d314.dxf')

print(f"Deep Analysis of DXF: {os.path.basename(path)}")

try:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    
    # 1. Analizar Capas (Layers)
    layers = [layer.dxf.name for layer in doc.layers]
    print(f"\n--- TOP LAYERS (Total: {len(layers)}) ---")
    print(", ".join(layers[:20]))
    
    # 2. Analizar Unidades
    insunits = doc.header.get('$INSUNITS', 0)
    units_map = {0: "Unspecified", 1: "Inches", 4: "Meters", 5: "Centimeters", 6: "Millimeters"}
    print(f"\nUnits: {units_map.get(insunits, f'Unknown {insunits}')}")
    
    # 3. Analizar Contenido de Texto (Keywords)
    all_texts = []
    for t in msp.query('TEXT MTEXT'):
        content = t.dxf.text if hasattr(t.dxf, 'text') else t.text
        all_texts.append(content.upper())
    
    keywords = ["AREA", "M2", "LOCAL", "NIVEL", "SALA", "WC", "COCINA", "OFICINA", "ESTACIONAMIENTO"]
    found_matches = [t for t in all_texts if any(k in t for k in keywords)]
    
    print(f"\n--- TEXT ANALYSIS ---")
    print(f"Total Text Entities: {len(all_texts)}")
    print(f"Relevant Keywords Found: {len(found_matches)}")
    if found_matches:
        print("Sample Relevant Text:")
        for m in found_matches[:10]: print(f"  - {m}")
        
    # 4. Analizar Bloques (Posibles luminarias o muebles)
    block_counts = Counter(insert.dxf.name for insert in msp.query('INSERT'))
    print(f"\n--- BLOCK COUNTS (Top 10) ---")
    for name, count in block_counts.most_common(10):
        print(f"  - {name}: {count}")

except Exception as e:
    print(f"Error: {e}")
