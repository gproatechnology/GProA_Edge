import ezdxf
import os

uploads_dir = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads'
dxf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.dxf')]

print(f"Inspecting {len(dxf_files)} DXF files...")

for fname in dxf_files:
    path = os.path.join(uploads_dir, fname)
    print(f"\n--- {fname} ---")
    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
        
        print(f"DXF Version: {doc.dxfversion}")
        print(f"Layers: {len(doc.layers)}")
        
        lwpolylines = msp.query('LWPOLYLINE')
        closed_polys = [p for p in lwpolylines if p.is_closed]
        print(f"Total LWPolylines: {len(lwpolylines)}")
        print(f"Closed LWPolylines: {len(closed_polys)}")
        
        if closed_polys:
            print("Sample areas (m2):")
            for p in closed_polys[:5]:
                try: print(f"  - Layer: {p.dxf.layer}, Area: {p.area():.2f}")
                except: pass
        
        texts = msp.query('TEXT MTEXT')
        print(f"Total Texts: {len(texts)}")
        if texts:
            print("Sample texts:")
            for t in texts[:5]:
                content = t.dxf.text if hasattr(t.dxf, 'text') else t.text
                print(f"  - Layer: {t.dxf.layer}, Content: {content[:50]}")
                
    except Exception as e:
        print(f"Error reading DXF: {e}")

