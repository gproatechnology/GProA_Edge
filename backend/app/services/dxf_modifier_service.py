import ezdxf
import logging
import os
from pathlib import Path
from app.core.config import logger

class DXFModifierService:
    def __init__(self):
        pass

    def apply_eosis_standards(self, file_path: str, config: dict = None) -> bool:
        """
        Applies EOSIS standards to a DXF file:
        - Creates 'EOSIS_Luis_COTAS_EDGE' layer.
        - Configures DimStyle.
        - Adds a reference dimension if possible.
        """
        if not os.path.exists(file_path) or not file_path.lower().endswith('.dxf'):
            return False

        try:
            doc = ezdxf.readfile(file_path)
            
            # 1. Ensure Layer exists
            layer_name = config.get('layer_name', 'EOSIS_Luis_COTAS_EDGE') if config else 'EOSIS_Luis_COTAS_EDGE'
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name, dxfattribs={'color': 1}) # Red as default for visibility
                logger.info(f"Layer {layer_name} created in {file_path}")

            # 2. Configure DimStyle (Standard)
            if 'Standard' in doc.dimstyles:
                dimstyle = doc.dimstyles.get('Standard')
                # Applying some 'Luis standards'
                dimstyle.dxf.dimtxt = 0.2 # Text height
                dimstyle.dxf.dimasz = 0.1 # Arrow size
            
            # 3. Add a sample dimension in the model space as a placeholder for 'Luis'
            msp = doc.modelspace()
            
            # We add a small dimension at the origin or near existing geometry
            # This serves as a "stamp" that the file has been processed
            msp.add_aligned_dim(
                p1=(0, 0), p2=(1, 0), distance=0.5,
                override={'layer': layer_name, 'text': 'PARAMETRIZADO EDGE'}
            )

            doc.save()
            return True
        except Exception as e:
            logger.error(f"Error modifying DXF {file_path}: {e}")
            return False

dxf_modifier_service = DXFModifierService()
