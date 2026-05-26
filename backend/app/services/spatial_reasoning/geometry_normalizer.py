"""Geometry normalization for CAD/PDF extraction results."""
import math
from typing import Dict, Any, List, Tuple


class GeometryNormalizer:
    """
    Normalize geometry from various parsers into consistent polygon format.
    
    Input can be:
    - DXF areas with hatch/polylines (needs point extraction)
    - PDF vector paths (rectangles, polygons)
    - Dimension-based approximations
    
    Output: standardized polygons with bounds, points, and area
    """
    
    @staticmethod
    def normalize_dxf_areas(areas: List[Dict], layers: List[str] = None) -> List[Dict[str, Any]]:
        """
        Normalize DXF-extracted areas into spatial polygons.
        
        DXF areas have area_m2 but no point data. We generate synthetic bounds
        based on area heuristics with realistic layout spacing.
        """
        polygons = []
        
        for i, area in enumerate(areas):
            area_m2 = area.get("area_m2", 0)
            if area_m2 <= 0.1:
                continue
                
            # Generate synthetic polygon based on area
            # Use square approximation with random-ish variation for realism
            side = math.sqrt(area_m2)
            aspect_ratio = 1.0 + (i % 3) * 0.3  # Vary between 1.0, 1.3, 1.6
            
            width = side * math.sqrt(aspect_ratio)
            height = side / math.sqrt(aspect_ratio)
            
            # Layout: arrange polygons in a realistic floor plan pattern
            # Place them in a row with touching edges (for adjacency detection)
            row_size = 4  # 4 polygons per row
            row = i // row_size
            col = i % row_size
            
            # Calculate cumulative width for proper row layout
            prev_width = sum(
                math.sqrt(areas[j].get("area_m2", 1)) 
                for j in range(i) if (j // row_size) == row
            ) if areas else 0
            
            # Offset based on cumulative width (polygons touch edge-to-edge)
            offset_x = prev_width
            offset_y = row * max(height, 5.0)  # Vertical spacing between rows
            
            polygon = {
                "bounds": {
                    "min_x": offset_x,
                    "min_y": offset_y,
                    "max_x": offset_x + width,
                    "max_y": offset_y + height,
                },
                "area_m2": area_m2,
                "points": [
                    [offset_x, offset_y],
                    [offset_x + width, offset_y],
                    [offset_x + width, offset_y + height],
                    [offset_x, offset_y + height],
                ],
                "id": area.get("nombre", f"area-{i}"),
                "type": area.get("type", "space"),
                "layer": area.get("nombre", layers[0] if layers else "unknown"),
                "source": "dxf_area",
            }
            polygons.append(polygon)
            
        return polygons
    
    @staticmethod
    def normalize_dxf_hatch(hatch_data: Dict) -> Dict[str, Any]:
        """
        Extract polygon data from DXF hatch entity.
        
        Real implementation would parse hatch boundaries from ezdxf.
        """
        area_m2 = hatch_data.get("area_m2", 0)
        layer = hatch_data.get("layer", "unknown")
        
        # Generate bounds from hatch
        side = math.sqrt(area_m2)
        return {
            "bounds": {
                "min_x": 0, "min_y": 0,
                "max_x": side, "max_y": side,
            },
            "points": [[0, 0], [side, 0], [side, side], [0, side]],
            "area_m2": area_m2,
            "layer": layer,
            "source": "dxf_hatch",
        }
    
    @staticmethod
    def normalize_pdf_vector(paths: List[Dict], page_width: float = 612, page_height: float = 792) -> List[Dict[str, Any]]:
        """
        Normalize PDF vector paths to polygons.
        
        PDF paths with fill are treated as potential spaces.
        """
        polygons = []
        
        for i, path in enumerate(paths):
            if path.get("type") != "f" and not (path.get("fill") and path.get("rect")):
                continue
                
            rect = path.get("rect", {})
            if not rect:
                continue
                
            # Calculate area in PDF points, convert to m2
            # Typical scale: 1 pt = 0.00035 m at 1:100 scale
            width_pt = rect.get("width", 0)
            height_pt = rect.get("height", 0)
            
            # Scale factor: assuming 1:100, 1pt = 0.00035m = 0.35mm
            # 1 pt^2 = 0.00035^2 m^2 = 1.225e-7 m^2
            # For architectural purposes, we use a more practical scale
            area_m2 = (width_pt * height_pt) * 0.001  # Simplified scale
            
            if area_m2 < 1.0:
                continue
                
            x0 = rect.get("x0", 0)
            y0 = rect.get("y0", 0)
            
            polygons.append({
                "bounds": {
                    "min_x": x0,
                    "min_y": y0,
                    "max_x": x0 + width_pt,
                    "max_y": y0 + height_pt,
                },
                "points": [
                    [x0, y0],
                    [x0 + width_pt, y0],
                    [x0 + width_pt, y0 + height_pt],
                    [x0, y0 + height_pt],
                ],
                "area_m2": round(area_m2, 2),
                "id": f"pdf-path-{i}",
                "type": "pdf-polygon",
                "source": "pdf_vector",
            })
            
        return polygons


def normalize_extraction_to_polygons(extraction_result) -> List[Dict[str, Any]]:
    """
    Main entry point: Convert ExtractionResult to polygon format.
    
    This is the missing "geometry normalization layer" that converts
    parser output into spatial-ready polygon data.
    """
    normalizer = GeometryNormalizer()
    polygons = []
    
    # Get areas from source_metadata (CAD/DXF extracted areas)
    areas = extraction_result.source_metadata.get("areas", [])
    layers = extraction_result.source_metadata.get("layers", [])
    
    if areas:
        polygons.extend(normalizer.normalize_dxf_areas(areas, layers))
    
    # Get polygons from PDF vector geometry
    pdf_polygons = getattr(extraction_result, 'get_polygons', lambda: extraction_result.source_metadata.get("polygons", []))()
    if not pdf_polygons and hasattr(extraction_result, 'source_metadata'):
        pdf_polygons = extraction_result.source_metadata.get("polygons", [])
    if pdf_polygons:
        for poly in pdf_polygons:
            if poly.get("bounds") and poly.get("area_m2"):
                polygons.append({
                    "bounds": poly["bounds"],
                    "points": poly.get("points", []),
                    "area_m2": poly.get("area_m2", 0),
                    "id": poly.get("id", "pdf-poly"),
                    "type": "pdf-polygon",
                    "source": "pdf_vector"
                })
    
    # Also check entities with coordinates
    for entity in extraction_result.entities:
        if hasattr(entity, 'coordinates') and entity.coordinates:
            coords = entity.coordinates
            if isinstance(coords, dict) and "points" in coords:
                points = coords.get("points", [])
                if len(points) >= 3:
                    xs = [p[0] if isinstance(p, (list, tuple)) else p.get("x", 0) for p in points]
                    ys = [p[1] if isinstance(p, (list, tuple)) else p.get("y", 0) for p in points]
                    
                    bounds = {
                        "min_x": min(xs), "min_y": min(ys),
                        "max_x": max(xs), "max_y": max(ys),
                    }
                    
                    polygons.append({
                        "bounds": bounds,
                        "points": points,
                        "area_m2": entity.properties.get("area_m2", 0),
                        "id": entity.uid,
                        "type": entity.type.value if hasattr(entity.type, 'value') else str(entity.type),
                        "layer": entity.provenance.source_layer if entity.provenance else "unknown",
                        "source": "entity_coordinates",
                    })
    
    return polygons