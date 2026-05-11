import fitz
import os

uploads_dir = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads'
files = sorted([f for f in os.listdir(uploads_dir) if f.endswith('.pdf')], key=lambda x: os.path.getmtime(os.path.join(uploads_dir, x)), reverse=True)

print(f"Inspecting the 3 most recent PDFs...")

for fname in files[:3]:
    path = os.path.join(uploads_dir, fname)
    print(f"\n--- {fname} ---")
    try:
        doc = fitz.open(path)
        print(f"Pages: {len(doc)}")
        text = doc[0].get_text()
        print(f"Text length on page 1: {len(text.strip())}")
        if len(text.strip()) > 0:
            print(f"Snippet: {text[:300].strip()}")
        else:
            print("PDF is likely SCANNED or VECTORIZED WITHOUT TEXT.")
        doc.close()
    except Exception as e:
        print(f"Error: {e}")
