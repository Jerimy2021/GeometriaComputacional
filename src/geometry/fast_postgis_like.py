"""
Sistema rápido tipo PostGIS para inserción masiva de puntos y consultas OSMnx
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
import logging
from scipy.spatial import cKDTree
import time
from .cgal_wrapper import GeometryAnalyzer
from ..data.csv_handler import CSVHandler, CrimeDataProcessor

logger = logging.getLogger(__name__)


class FastPostGISLike:
    """
    Sistema rápido tipo PostGIS para análisis geoespacial
    Usa técnicas de inserción masiva y consultas optimizadas
    """
    
    def __init__(self):
        self.geometry_analyzer = GeometryAnalyzer()
        self.points: List[Tuple[float, float]] = []
        self.points_array: Optional[np.ndarray] = None
        self.kdtree: Optional[cKDTree] = None
        self.results: Dict[str, Any] = {}
        self.osmnx_graph = None
        
    def bulk_insert_points(self, csv_path: str, batch_size: int = 10000) -> bool:
        """
        Inserción masiva de puntos como en PostGIS
        
        Args:
            csv_path: Ruta al archivo CSV
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            True si la inserción fue exitosa
        """
        try:
            print("🚀 Iniciando inserción masiva de puntos...")
            start_time = time.time()
            
            # Cargar datos en lotes
            processor = CrimeDataProcessor()
            csv_handler = CSVHandler(processor)
            
            if not csv_handler.load_csv(csv_path):
                return False
            
            # Procesar en lotes para mejor rendimiento
            df = csv_handler.get_dataframe()
            if df is None:
                return False
            
            # Filtrar y convertir coordenadas en lote
            valid_data = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
            valid_data['LATITUDE'] = valid_data['LATITUDE'].astype(str).str.replace(',', '.').astype(float)
            valid_data['LONGITUDE'] = valid_data['LONGITUDE'].astype(str).str.replace(',', '.').astype(float)
            
            # Filtrar por región de São Paulo
            valid_data = valid_data[
                (valid_data['LATITUDE'] >= -24.0) & (valid_data['LATITUDE'] <= -23.0) &
                (valid_data['LONGITUDE'] >= -47.0) & (valid_data['LONGITUDE'] <= -46.0)
            ]
            
            # Convertir a lista de tuplas
            self.points = list(zip(valid_data['LATITUDE'], valid_data['LONGITUDE']))
            
            # Crear array numpy para operaciones rápidas
            self.points_array = np.array(self.points)
            
            # Construir KDTree para consultas espaciales rápidas
            print("🌳 Construyendo índice espacial...")
            self.kdtree = cKDTree(self.points_array)
            
            insert_time = time.time() - start_time
            print(f"✅ {len(self.points)} puntos insertados en {insert_time:.2f} segundos")
            print(f"📊 Velocidad: {len(self.points)/insert_time:.0f} puntos/segundo")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en inserción masiva: {e}")
            return False
    
    def fast_spatial_query(self, center: Tuple[float, float], radius_km: float) -> List[int]:
        """
        Consulta espacial rápida tipo PostGIS ST_DWithin
        
        Args:
            center: Centro de la consulta (lat, lon)
            radius_km: Radio en kilómetros
            
        Returns:
            Índices de puntos dentro del radio
        """
        if self.kdtree is None:
            return []
        
        try:
            # Convertir radio de km a grados (aproximado)
            lat_center, lon_center = center
            lat_radius = radius_km / 111.32  # km por grado de latitud
            lon_radius = radius_km / (111.32 * abs(lat_center) * np.pi / 180)  # km por grado de longitud
            
            # Consulta en KDTree
            indices = self.kdtree.query_ball_point(center, max(lat_radius, lon_radius))
            
            return indices
            
        except Exception as e:
            logger.error(f"Error en consulta espacial: {e}")
            return []
    
    def fast_nearest_points(self, query_points: List[Tuple[float, float]], k: int = 1) -> List[List[int]]:
        """
        Encuentra k puntos más cercanos para cada punto de consulta
        
        Args:
            query_points: Puntos de consulta
            k: Número de puntos más cercanos
            
        Returns:
            Lista de listas con índices de puntos más cercanos
        """
        if self.kdtree is None:
            return []
        
        try:
            query_array = np.array(query_points)
            distances, indices = self.kdtree.query(query_array, k=k)
            
            if k == 1:
                return [[idx] for idx in indices]
            else:
                return [list(idx_list) for idx_list in indices]
                
        except Exception as e:
            logger.error(f"Error en búsqueda de vecinos: {e}")
            return []
    
    def fast_geometry_analysis(self) -> Dict[str, Any]:
        """
        Análisis geométrico rápido usando CGAL
        """
        if not self.points:
            return {}
        
        try:
            print("🔍 Realizando análisis geométrico con CGAL...")
            start_time = time.time()
            
            # Usar solo una muestra para análisis rápido si hay muchos puntos
            sample_size = min(5000, len(self.points))
            if len(self.points) > sample_size:
                import random
                sample_points = random.sample(self.points, sample_size)
                print(f"📊 Usando muestra de {sample_size} puntos para análisis")
            else:
                sample_points = self.points
            
            # Análisis geométrico
            results = self.geometry_analyzer.analyze_point_distribution(sample_points)
            
            analysis_time = time.time() - start_time
            print(f"✅ Análisis completado en {analysis_time:.2f} segundos")
            
            # Añadir estadísticas de rendimiento
            results['performance'] = {
                'analysis_time': analysis_time,
                'points_analyzed': len(sample_points),
                'points_per_second': len(sample_points) / analysis_time
            }
            
            self.results = results
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis geométrico: {e}")
            return {}
    
    def create_osmnx_graph_fast(self, place_name: str = "São Paulo, Brazil") -> bool:
        """
        Crea grafo OSMnx de manera optimizada
        """
        try:
            import osmnx as ox
            
            print(f"🗺️  Creando grafo de {place_name}...")
            start_time = time.time()
            
            # Configurar OSMnx para mejor rendimiento
            ox.config(use_cache=True, log_console=False)
            
            # Crear grafo simplificado
            self.osmnx_graph = ox.graph_from_place(
                place_name,
                network_type='drive',  # Solo carreteras para mejor rendimiento
                simplify=True
            )
            
            graph_time = time.time() - start_time
            print(f"✅ Grafo creado: {len(self.osmnx_graph.nodes)} nodos, {len(self.osmnx_graph.edges)} aristas")
            print(f"⏱️  Tiempo: {graph_time:.2f} segundos")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creando grafo OSMnx: {e}")
            return False
    
    def fast_osmnx_integration(self, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Integración rápida con OSMnx usando solo una muestra
        """
        if not self.osmnx_graph or not self.points:
            return {}
        
        try:
            import osmnx as ox
            
            print(f"🔗 Integrando {min(sample_size, len(self.points))} puntos con OSMnx...")
            start_time = time.time()
            
            # Usar solo una muestra para integración rápida
            sample_points = self.points[:sample_size] if len(self.points) > sample_size else self.points
            
            # Encontrar nodos más cercanos en lote
            lons = [p[1] for p in sample_points]
            lats = [p[0] for p in sample_points]
            
            nearest_nodes = ox.distance.nearest_nodes(
                self.osmnx_graph, 
                X=lons, 
                Y=lats
            )
            
            integration_time = time.time() - start_time
            print(f"✅ Integración completada en {integration_time:.2f} segundos")
            
            # Calcular algunas rutas de ejemplo
            routes = []
            if len(nearest_nodes) > 1:
                # Calcular rutas entre algunos puntos aleatorios
                import random
                sample_routes = min(10, len(nearest_nodes) // 2)
                route_pairs = random.sample(list(nearest_nodes), sample_routes * 2)
                
                for i in range(0, len(route_pairs), 2):
                    try:
                        route = ox.distance.shortest_path(
                            self.osmnx_graph, 
                            route_pairs[i], 
                            route_pairs[i+1]
                        )
                        if route:
                            routes.append(route)
                    except:
                        continue
            
            return {
                'nearest_nodes': nearest_nodes,
                'routes_calculated': len(routes),
                'integration_time': integration_time,
                'points_per_second': len(sample_points) / integration_time
            }
            
        except Exception as e:
            logger.error(f"Error en integración OSMnx: {e}")
            return {}
    
    def benchmark_queries(self) -> Dict[str, float]:
        """
        Benchmark de consultas espaciales
        """
        if not self.points:
            return {}
        
        print("\n🏁 BENCHMARK DE CONSULTAS ESPACIALES")
        
        # Consulta por radio
        center = (-23.5505, -46.6333)  # Centro de São Paulo
        radius_km = 5.0
        
        start = time.time()
        radius_results = self.fast_spatial_query(center, radius_km)
        radius_time = time.time() - start
        
        # Consulta de vecinos más cercanos
        query_points = self.points[:100]  # 100 puntos de consulta
        
        start = time.time()
        nearest_results = self.fast_nearest_points(query_points, k=5)
        nearest_time = time.time() - start
        
        print(f"📍 Consulta por radio (5km): {len(radius_results)} puntos en {radius_time:.4f}s")
        print(f"🔍 Consulta vecinos (100 puntos): {nearest_time:.4f}s")
        
        return {
            'radius_query_time': radius_time,
            'nearest_query_time': nearest_time,
            'radius_points_found': len(radius_results),
            'queries_per_second': 100 / nearest_time
        }
    
    def export_to_geojson(self, output_path: str) -> bool:
        """
        Exporta puntos a GeoJSON para visualización
        """
        try:
            import json
            
            features = []
            for i, (lat, lon) in enumerate(self.points):
                feature = {
                    "type": "Feature",
                    "properties": {"id": i},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    }
                }
                features.append(feature)
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            with open(output_path, 'w') as f:
                json.dump(geojson, f)
            
            print(f"📁 GeoJSON exportado a: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando GeoJSON: {e}")
            return False
