"""
Wrapper de CGAL para operaciones geométricas
Implementa el patrón Facade para simplificar el uso de CGAL
"""

import numpy as np
from typing import List, Tuple, Optional
import logging

try:
    import compas_cgal
    from compas_cgal import triangulation
    CGAL_AVAILABLE = True
except ImportError:
    CGAL_AVAILABLE = False
    logging.warning("CGAL no está disponible. Instalar con: conda create -n cgal -c conda-forge compas compas_cgal")

logger = logging.getLogger(__name__)


class CGALWrapper:
    """Wrapper principal para operaciones de CGAL"""
    
    def __init__(self):
        if not CGAL_AVAILABLE:
            raise ImportError("CGAL no está disponible. Instalar con: conda create -n cgal -c conda-forge compas compas_cgal")
    
    def delaunay_triangulation_2d(self, points: List[Tuple[float, float]]) -> List[Tuple[int, int, int]]:
        """
        Realiza triangulación de Delaunay 2D
        
        Args:
            points: Lista de puntos (x, y)
            
        Returns:
            Lista de triángulos como índices (i, j, k)
        """
        try:
            # Convertir puntos a numpy array
            points_array = np.array(points, dtype=np.float64)
            
            # Realizar triangulación de Delaunay
            triangles = triangulation.delaunay_triangulation_2d(points_array)
            
            logger.info(f"Triangulación completada: {len(triangles)} triángulos")
            return triangles.tolist()
            
        except Exception as e:
            logger.error(f"Error en triangulación de Delaunay: {e}")
            return []
    
    def convex_hull_2d(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Calcula la envolvente convexa 2D
        
        Args:
            points: Lista de puntos (x, y)
            
        Returns:
            Lista de puntos de la envolvente convexa
        """
        try:
            points_array = np.array(points, dtype=np.float64)
            hull_points = triangulation.convex_hull_2d(points_array)
            
            logger.info(f"Envolvente convexa calculada: {len(hull_points)} puntos")
            return hull_points.tolist()
            
        except Exception as e:
            logger.error(f"Error calculando envolvente convexa: {e}")
            return []
    
    def voronoi_diagram_2d(self, points: List[Tuple[float, float]]) -> dict:
        """
        Calcula el diagrama de Voronoi 2D
        
        Args:
            points: Lista de puntos (x, y)
            
        Returns:
            Diccionario con vértices y celdas del diagrama de Voronoi
        """
        try:
            points_array = np.array(points, dtype=np.float64)
            voronoi_result = triangulation.voronoi_diagram_2d(points_array)
            
            logger.info("Diagrama de Voronoi calculado exitosamente")
            return {
                'vertices': voronoi_result['vertices'].tolist(),
                'cells': voronoi_result['cells'].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error calculando diagrama de Voronoi: {e}")
            return {'vertices': [], 'cells': []}
    
    def point_in_polygon(self, point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
        """
        Verifica si un punto está dentro de un polígono
        
        Args:
            point: Punto a verificar (x, y)
            polygon: Lista de puntos del polígono
            
        Returns:
            True si el punto está dentro del polígono
        """
        try:
            # Implementación simple del algoritmo ray casting
            x, y = point
            n = len(polygon)
            inside = False
            
            p1x, p1y = polygon[0]
            for i in range(1, n + 1):
                p2x, p2y = polygon[i % n]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x, p1y = p2x, p2y
            
            return inside
            
        except Exception as e:
            logger.error(f"Error verificando punto en polígono: {e}")
            return False


class GeometryAnalyzer:
    """Analizador geométrico que usa CGALWrapper"""
    
    def __init__(self):
        self.cgal = CGALWrapper()
    
    def analyze_point_distribution(self, points: List[Tuple[float, float]]) -> dict:
        """
        Analiza la distribución de puntos usando varias técnicas geométricas
        
        Args:
            points: Lista de puntos (lat, lon)
            
        Returns:
            Diccionario con resultados del análisis
        """
        if not points:
            return {}
        
        # Convertir coordenadas geográficas a coordenadas planas (aproximación)
        # Para São Paulo, usamos una proyección simple
        projected_points = self._geographic_to_projected(points)
        
        results = {
            'total_points': len(points),
            'delaunay_triangles': self.cgal.delaunay_triangulation_2d(projected_points),
            'convex_hull': self.cgal.convex_hull_2d(projected_points),
            'voronoi_diagram': self.cgal.voronoi_diagram_2d(projected_points)
        }
        
        return results
    
    def _geographic_to_projected(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Convierte coordenadas geográficas a coordenadas planas (aproximación simple)
        Para São Paulo, centro aproximado: -23.5505, -46.6333
        """
        center_lat, center_lon = -23.5505, -46.6333
        
        projected = []
        for lat, lon in points:
            # Conversión simple (no es una proyección cartográfica real)
            x = (lon - center_lon) * 111320 * np.cos(np.radians(lat))
            y = (lat - center_lat) * 111320
            projected.append((x, y))
        
        return projected
