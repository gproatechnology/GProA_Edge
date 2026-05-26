import asyncio
import os
import sys

# Añadir el directorio actual al path para importar 'app'
sys.path.append(os.getcwd())

from app.services.technical_extraction_engine import engine

async def run_test():
    file_path = 'docs/Documentos_EOSIS/Tristone_Area Breakdown_Layout.pdf'
    # Ajustar path si es necesario (asumiendo ejecución desde backend/)
    # Si estamos en backend/, el path real al archivo es ../docs/...
    actual_path = os.path.join('..', file_path)
    
    if not os.path.exists(actual_path):
        print(f"❌ Archivo no encontrado en: {actual_path}")
        return

    print(f"--- Iniciando Extracción de Prueba: {os.path.basename(actual_path)} ---")
    try:
        result = await engine.extract(actual_path)
        
        print(f"✅ Extracción completada.")
        print(f"📊 Entidades encontradas: {len(result.entities)}")
        print(f"🛡️ Confianza Global: {result.confidence}")
        
        if result.entities:
            print("\n🔍 Muestra de Entidades (Top 3):")
            for e in result.entities[:3]:
                # Usamos .uid gracias a nuestra refactorización v1.0
                print(f"  - [{e.uid}] Tipo: {e.type} | Propiedades: {e.properties}")
        else:
            print("\n⚠️ No se extrajeron entidades. Esto puede deberse a que el PDF es escaneado o el parser necesita ajustes específicos.")
            
        if result.warnings:
            print("\n⚠️ Warnings:")
            for w in result.warnings:
                print(f"  - {w}")

    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
