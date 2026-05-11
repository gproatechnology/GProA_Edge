import ezdxf
import os
from collections import Counter

path = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads\1f7de668-d83f-4256-93ab-956c67d08b83.dxf'

print(f"AUTOPSIA REAL: {os.path.basename(path)}")

try:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    
    # 1. Contar TODO lo que hay en el espacio de modelo
    all_entities = [e.dxftype() for e in msp]
    print(f"\n--- ENTIDADES TOTALES ({len(all_entities)}) ---")
    for type, count in Counter(all_entities).most_common():
        print(f"  {type}: {count}")
        
    # 2. Ver contenidos de TEXTO
    print(f"\n--- MUESTRA DE TEXTOS ---")
    texts = msp.query('TEXT MTEXT')
    for t in texts[:20]:
        val = t.dxf.text if hasattr(t.dxf, 'text') else t.text
        print(f"  {val.strip()}")

    # 3. Ver Bloques e INSERTS
    print(f"\n--- BLOQUES UTILIZADOS (INSERTS) ---")
    inserts = msp.query('INSERT')
    block_names = Counter(i.dxf.name for i in inserts)
    for name, count in block_names.most_common(10):
        print(f"  Bloque '{name}': {count} veces")

except Exception as e:
    print(f"Error: {e}")
