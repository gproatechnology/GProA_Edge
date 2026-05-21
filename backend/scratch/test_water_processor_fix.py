import sys
import os
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

# Set dummy env vars if not present
os.environ.setdefault("DEMO_MODE", "true")

from app.services.edge_processors import run_specialized_processor

async def main():
    print("--- TESTING WATER PROCESSOR DISPATCH FIX ---")
    
    # Test case 1: WEM01 (Water measure - Faucets)
    print("\n1. Testing WEM01 (Water Faucets) - Should use process_water_fixtures")
    content_wem01 = "Ficha Tecnica: Griferia marca Grohe modelo Eurosmart, flujo 5.5 LPM, cantidad 10"
    try:
        res_wem01 = await run_specialized_processor("WEM01", content_wem01, api_key=None)
        print("Success! Result:")
        print(res_wem01)
        assert res_wem01 is not None
        assert "aparatos" in res_wem01
        print("WEM01 Dispatch Check: PASSED")
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()

    # Test case 2: WEM02 (Water measure - Toilets)
    print("\n2. Testing WEM02 (Water Toilets) - Should use process_water_fixtures")
    content_wem02 = "Inodoro marca Toto, flujo 4.5 LPF, cantidad 5"
    try:
        res_wem02 = await run_specialized_processor("WEM02", content_wem02, api_key=None)
        print("Success! Result:")
        print(res_wem02)
        assert res_wem02 is not None
        assert "aparatos" in res_wem02
        print("WEM02 Dispatch Check: PASSED")
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()

    # Test case 3: EEM22 (Lighting - Energy measure)
    print("\n3. Testing EEM22 (Lighting) - Should use process_eem22_luminaires")
    content_eem22 = "Luminaria LED, 12W, 1320 lumens, cantidad 20"
    try:
        res_eem22 = await run_specialized_processor("EEM22", content_eem22, api_key=None)
        print("Success! Result:")
        print(res_eem22)
        assert res_eem22 is not None
        print("EEM22 Dispatch Check: PASSED")
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- ALL TESTS COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(main())
