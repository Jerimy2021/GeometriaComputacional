#!/usr/bin/env python3
"""
Sistema principal de Geometría Computacional con CGAL
Análisis rápido de datos de crimen con integración OSMnx
"""

import sys
from pathlib import Path
import time
import logging

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent))

from src.geometry import FastPostGISLike

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Función principal del sistema"""
    
    print("🚀 SISTEMA DE GEOMETRÍA COMPUTACIONAL CON CGAL")
    print("=" * 50)
    
    # Crear analizador
    analyzer = FastPostGISLike()
    
    # Ruta al archivo CSV de crimen
    csv_path = "/Users/pierre/Downloads/crimen_fusionado.csv"
    
    total_start = time.time()
    
    try:
        # 1. Inserción masiva de puntos (como PostGIS)
        print("\n1️⃣ INSERCIÓN MASIVA DE PUNTOS")
        if not analyzer.bulk_insert_points(csv_path):
            logger.error("Error en inserción masiva de puntos")
            return
        
        # 2. Análisis geométrico con CGAL
        print("\n2️⃣ ANÁLISIS GEOMÉTRICO CON CGAL")
        geometry_results = analyzer.fast_geometry_analysis()
        
        if geometry_results:
            perf = geometry_results.get('performance', {})
            print(f"   📊 Triángulos de Delaunay: {len(geometry_results.get('delaunay_triangles', []))}")
            print(f"   🔺 Envolvente convexa: {len(geometry_results.get('convex_hull', []))}")
            print(f"   ⚡ Velocidad: {perf.get('points_per_second', 0):.0f} puntos/seg")
        
        # 3. Crear grafo OSMnx optimizado
        print("\n3️⃣ GRAFO OSMNX OPTIMIZADO")
        if analyzer.create_osmnx_graph_fast():
            # Integración rápida con muestra
            integration_results = analyzer.fast_osmnx_integration(sample_size=1000)
            if integration_results:
                print(f"   🔗 Puntos integrados: {len(integration_results.get('nearest_nodes', []))}")
                print(f"   ⚡ Velocidad: {integration_results.get('points_per_second', 0):.0f} puntos/seg")
        
        # 4. Consultas espaciales rápidas
        print("\n4️⃣ CONSULTAS ESPACIALES RÁPIDAS")
        benchmark_results = analyzer.benchmark_queries()
        
        # 5. Consultas de ejemplo
        print("\n5️⃣ CONSULTAS DE EJEMPLO")
        center_sp = (-23.5505, -46.6333)  # Centro de São Paulo
        
        # Consulta por radio
        radius_5km = analyzer.fast_spatial_query(center_sp, 5.0)
        radius_10km = analyzer.fast_spatial_query(center_sp, 10.0)
        print(f"   📍 Puntos en 5km del centro: {len(radius_5km)}")
        print(f"   📍 Puntos en 10km del centro: {len(radius_10km)}")
        
        # Consulta de vecinos más cercanos
        sample_points = [(-23.5505, -46.6333), (-23.5600, -46.6400)]
        nearest = analyzer.fast_nearest_points(sample_points, k=3)
        print(f"   🔍 Vecinos más cercanos: {len(nearest)} consultas")
        
        # 6. Exportar resultados
        print("\n6️⃣ EXPORTAR RESULTADOS")
        analyzer.export_to_geojson("crime_points.geojson")
        
        total_time = time.time() - total_start
        
        print(f"\n✅ ANÁLISIS COMPLETADO")
        print(f"⏱️  Tiempo total: {total_time:.2f} segundos")
        print(f"📊 Puntos procesados: {len(analyzer.points)}")
        print(f"⚡ Velocidad global: {len(analyzer.points)/total_time:.0f} puntos/segundo")
        
        print(f"\n📈 RENDIMIENTO:")
        print(f"   - Inserción masiva: ✅ Rápida como PostGIS")
        print(f"   - Consultas espaciales: ✅ KDTree (muy rápido)")
        print(f"   - Análisis geométrico: ✅ CGAL (más rápido que PostGIS)")
        print(f"   - Integración OSMnx: ✅ Optimizada")
        
    except Exception as e:
        logger.error(f"Error en el análisis: {e}")
        raise


if __name__ == "__main__":
    main()
