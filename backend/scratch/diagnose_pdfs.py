import fitz
import os
import pdfplumber

uploads_dir = r'c:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\backend\uploads'
files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]

print(f"Checking {len(files)} PDFs in uploads directory...")

for fname in files:
    path = os.path.join(uploads_dir, fname)
    size = os.path.getsize(path)
    
    print(f"\n--- FILE: {fname} ({size/1024:.1f} KB) ---")
    
    # 1. Check with Fitz (Fast text check)
    try:
        doc = fitz.open(path)
        text = ""
        for i in range(min(3, len(doc))): # Check first 3 pages
            text += doc[i].get_text()
        doc.close()
        
        text_len = len(text.strip())
        print(f"Fitz Searchable Text Length: {text_len}")
        if text_len > 100:
            print(f"Sample Text: {text[:200].replace('\n', ' ')}")
        else:
            print(" Fitz: NO SEARCHABLE TEXT DETECTED.")
            
    except Exception as e:
        print(f"Fitz Error: {e}")

    # 2. Check with pdfplumber (Tables check)
    try:
        with pdfplumber.open(path) as pdf:
            tables_count = 0
            for page in pdf.pages[:2]: # Check first 2 pages
                tbls = page.extract_tables()
                if tbls:
                    tables_count += len(tbls)
            print(f"PdfPlumber Tables Detected: {tables_count}")
    except Exception as e:
        print(f"PdfPlumber Error: {e}")

