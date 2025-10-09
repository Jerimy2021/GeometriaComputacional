#!/usr/bin/env python3
"""
Visualización del mapa de São Paulo con puntos de crimen
"""

import sys
from pathlib import Path
import time
import logging

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent))

from src.geometry import FastPostGISLike
import matplotlib.pyplot as plt
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_map_visualization():
    """Crea visualización del mapa de São Paulo con puntos de crimen"""
    
    print("🗺️  CREANDO MAPA DE SÃO PAULO CON PUNTOS DE CRIMEN")
    print("=" * 60)
    
    # Crear analizador
    analyzer = FastPostGISLike()
    
    # Ruta al CSV
    csv_path = "/Users/pierre/Downloads/crimen_fusionado.csv"
    
    start_time = time.time()
    
    try:
        # 1. Cargar datos
        print("📊 Cargando datos de crimen...")
        if not analyzer.bulk_insert_points(csv_path):
            print("❌ Error cargando datos")
            return
        
        load_time = time.time()
        print(f"✅ {len(analyzer.points)} puntos cargados en {load_time - start_time:.2f}s")
        
        # 2. Crear grafo OSMnx
        print("🗺️  Creando grafo de São Paulo...")
        if not analyzer.create_osmnx_graph_fast():
            print("❌ Error creando grafo OSMnx")
            return
        
        graph_time = time.time()
        print(f"✅ Grafo creado en {graph_time - load_time:.2f}s")
        
        # 3. Preparar datos para visualización
        print("🎨 Preparando datos para visualización...")
        
        # Convertir puntos a arrays
        points_array = np.array(analyzer.points)
        lats = points_array[:, 0]
        lons = points_array[:, 1]
        
        # Crear figura
        fig, ax = plt.subplots(1, 1, figsize=(15, 12))
        
        # 4. Visualizar grafo de calles
        print("🛣️  Dibujando calles...")
        try:
            import osmnx as ox
            
            # Dibujar grafo
            ox.plot_graph(
                analyzer.osmnx_graph,
                ax=ax,
                node_size=0,
                edge_linewidth=0.5,
                edge_color='lightgray',
                show=False,
                close=False
            )
        except Exception as e:
            print(f"⚠️  Error dibujando grafo: {e}")
        
        # 5. Visualizar puntos de crimen
        print("🔴 Dibujando puntos de crimen...")
        
        # Usar una muestra para mejor rendimiento
        sample_size = min(10000, len(points_array))
        if len(points_array) > sample_size:
            indices = np.random.choice(len(points_array), sample_size, replace=False)
            sample_lats = lats[indices]
            sample_lons = lons[indices]
        else:
            sample_lats = lats
            sample_lons = lons
        
        # Dibujar puntos con transparencia
        scatter = ax.scatter(
            sample_lons, sample_lats,
            c='red', s=1, alpha=0.6,
            label=f'Puntos de crimen ({len(sample_lats)})'
        )
        
        # 6. Añadir hotspots (áreas de alta densidad)
        print("🔥 Identificando hotspots...")
        try:
            # Calcular densidad usando grilla
            from scipy.stats import gaussian_kde
            
            # Crear grilla
            x_min, x_max = lons.min(), lons.max()
            y_min, y_max = lats.min(), lats.max()
            
            # Muestrear para densidad
            density_sample = min(5000, len(points_array))
            if len(points_array) > density_sample:
                density_indices = np.random.choice(len(points_array), density_sample, replace=False)
                density_lons = lons[density_indices]
                density_lats = lats[density_indices]
            else:
                density_lons = lons
                density_lats = lats
            
            # Calcular densidad
            try:
                density = gaussian_kde(np.vstack([density_lons, density_lats]))
                
                # Crear grilla para densidad
                xx, yy = np.mgrid[x_min:x_max:100j, y_min:y_max:100j]
                positions = np.vstack([xx.ravel(), yy.ravel()])
                density_values = density(positions).reshape(xx.shape)
                
                # Dibujar contornos de densidad
                contour = ax.contour(xx, yy, density_values, levels=5, colors='orange', alpha=0.7, linewidths=1)
                ax.clabel(contour, inline=True, fontsize=8)
                
            except Exception as e:
                print(f"⚠️  Error calculando densidad: {e}")
                
        except ImportError:
            print("⚠️  scipy no disponible para análisis de densidad")
        
        # 7. Configurar mapa
        ax.set_xlabel('Longitud', fontsize=12)
        ax.set_ylabel('Latitud', fontsize=12)
        ax.set_title('Mapa de São Paulo - Puntos de Crimen', fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Ajustar límites
        margin = 0.01
        ax.set_xlim(lons.min() - margin, lons.max() + margin)
        ax.set_ylim(lats.min() - margin, lats.max() + margin)
        
        # 8. Guardar mapa
        print("💾 Guardando mapa...")
        plt.tight_layout()
        plt.savefig('sao_paulo_crime_map.png', dpi=300, bbox_inches='tight')
        plt.savefig('sao_paulo_crime_map.pdf', bbox_inches='tight')
        
        # Mostrar estadísticas
        total_time = time.time() - start_time
        print(f"\n✅ MAPA CREADO EXITOSAMENTE")
        print(f"⏱️  Tiempo total: {total_time:.2f} segundos")
        print(f"📊 Puntos visualizados: {len(sample_lats)}")
        print(f"🗺️  Archivos guardados:")
        print(f"   - sao_paulo_crime_map.png (alta resolución)")
        print(f"   - sao_paulo_crime_map.pdf (vectorial)")
        
        # Mostrar mapa
        plt.show()
        
    except Exception as e:
        logger.error(f"Error creando visualización: {e}")
        print(f"❌ Error: {e}")


def create_detailed_analysis():
    """Crea análisis detallado con múltiples visualizaciones"""
    
    print("\n📊 ANÁLISIS DETALLADO")
    print("=" * 30)
    
    analyzer = FastPostGISLike()
    
    if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
        return
    
    # Análisis por regiones
    regions = {
        "Centro": (-23.5505, -46.6333, 5.0),
        "Zona Sul": (-23.6000, -46.7000, 8.0),
        "Zona Norte": (-23.5000, -46.6000, 8.0),
        "Zona Leste": (-23.5500, -46.5000, 8.0),
        "Zona Oeste": (-23.5500, -46.8000, 8.0)
    }
    
    print("📍 Análisis por regiones:")
    for region, (lat, lon, radius) in regions.items():
        points = analyzer.fast_spatial_query((lat, lon), radius)
        print(f"   {region}: {len(points)} puntos")
    
    # Análisis temporal (si hay datos de fecha)
    print("\n📅 Análisis temporal:")
    print("   (Requiere procesamiento adicional de fechas)")


if __name__ == "__main__":
    # Crear visualización principal
    create_map_visualization()
    
    # Crear análisis detallado
    create_detailed_analysis()
    
    print("\n🎉 ¡Visualización completada!")
    print("💡 Abre los archivos PNG/PDF para ver el mapa completo")
