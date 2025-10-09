#!/usr/bin/env python3
"""
Visualización del mapa de São Paulo con puntos de crimen - VERSIÓN CORREGIDA
"""

import sys
from pathlib import Path
import time
import logging
import matplotlib.pyplot as plt
import numpy as np

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent))

from src.geometry import FastPostGISLike

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_map_with_osmnx():
    """Crea mapa usando OSMnx correctamente"""
    
    print("🗺️  CREANDO MAPA DE SÃO PAULO CON OSMNX")
    print("=" * 50)
    
    try:
        import osmnx as ox
        print("✅ OSMnx importado correctamente")
        
        # Crear analizador
        analyzer = FastPostGISLike()
        
        # Cargar datos
        print("📊 Cargando datos de crimen...")
        if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
            print("❌ Error cargando datos")
            return
        
        print(f"✅ {len(analyzer.points)} puntos cargados")
        
        # Crear grafo OSMnx
        print("🗺️  Creando grafo de São Paulo...")
        
        # Configurar OSMnx
        try:
            ox.config(use_cache=True, log_console=False)
        except:
            print("⚠️  OSMnx config no disponible, continuando...")
        
        # Crear grafo
        G = ox.graph_from_place(
            "São Paulo, Brazil",
            network_type='drive',
            simplify=True
        )
        
        print(f"✅ Grafo creado: {len(G.nodes)} nodos, {len(G.edges)} aristas")
        
        # Crear figura
        fig, ax = plt.subplots(1, 1, figsize=(20, 16))
        
        # Dibujar grafo de calles
        print("🛣️  Dibujando calles...")
        ox.plot_graph(
            G,
            ax=ax,
            node_size=0,
            edge_linewidth=0.3,
            edge_color='lightblue',
            show=False,
            close=False
        )
        
        # Preparar puntos de crimen
        points_array = np.array(analyzer.points)
        lats = points_array[:, 0]
        lons = points_array[:, 1]
        
        # Usar muestra para mejor rendimiento
        sample_size = min(20000, len(points_array))
        if len(points_array) > sample_size:
            indices = np.random.choice(len(points_array), sample_size, replace=False)
            sample_lats = lats[indices]
            sample_lons = lons[indices]
        else:
            sample_lats = lats
            sample_lons = lons
        
        # Dibujar puntos de crimen
        print("🔴 Dibujando puntos de crimen...")
        ax.scatter(
            sample_lons, sample_lats,
            c='red', s=0.5, alpha=0.7,
            label=f'Puntos de crimen ({len(sample_lats)})'
        )
        
        # Configurar mapa
        ax.set_xlabel('Longitud', fontsize=14)
        ax.set_ylabel('Latitud', fontsize=14)
        ax.set_title('Mapa de São Paulo - Puntos de Crimen', fontsize=18, fontweight='bold')
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Ajustar límites
        margin = 0.005
        ax.set_xlim(lons.min() - margin, lons.max() + margin)
        ax.set_ylim(lats.min() - margin, lats.max() + margin)
        
        # Guardar mapa
        print("💾 Guardando mapa...")
        plt.tight_layout()
        plt.savefig('sao_paulo_crime_map_osmnx.png', dpi=300, bbox_inches='tight')
        plt.savefig('sao_paulo_crime_map_osmnx.pdf', bbox_inches='tight')
        
        print("✅ Mapa guardado como sao_paulo_crime_map_osmnx.png")
        
        # Mostrar mapa
        plt.show()
        
    except ImportError as e:
        print(f"❌ Error importando OSMnx: {e}")
        print("💡 Instalando OSMnx...")
        import subprocess
        subprocess.run(["pip", "install", "osmnx"], check=True)
        print("✅ OSMnx instalado, ejecuta de nuevo")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def create_simple_map():
    """Crea mapa simple sin OSMnx"""
    
    print("\n🗺️  CREANDO MAPA SIMPLE (SIN OSMNX)")
    print("=" * 40)
    
    # Crear analizador
    analyzer = FastPostGISLike()
    
    # Cargar datos
    if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
        print("❌ Error cargando datos")
        return
    
    # Preparar datos
    points_array = np.array(analyzer.points)
    lats = points_array[:, 0]
    lons = points_array[:, 1]
    
    # Crear figura
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Dibujar puntos de crimen
    print("🔴 Dibujando puntos de crimen...")
    
    # Usar muestra para mejor rendimiento
    sample_size = min(50000, len(points_array))
    if len(points_array) > sample_size:
        indices = np.random.choice(len(points_array), sample_size, replace=False)
        sample_lats = lats[indices]
        sample_lons = lons[indices]
    else:
        sample_lats = lats
        sample_lons = lons
    
    # Crear mapa de calor
    ax.hexbin(sample_lons, sample_lats, gridsize=50, cmap='Reds', alpha=0.8)
    
    # Dibujar algunos puntos individuales
    ax.scatter(
        sample_lons[::100], sample_lats[::100],  # Cada 100 puntos
        c='darkred', s=1, alpha=0.6
    )
    
    # Configurar mapa
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    ax.set_title('Mapa de São Paulo - Densidad de Crimen', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Añadir información
    ax.text(0.02, 0.98, f'Puntos mostrados: {len(sample_lats):,}', 
            transform=ax.transAxes, fontsize=10, 
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            verticalalignment='top')
    
    # Guardar mapa
    print("💾 Guardando mapa...")
    plt.tight_layout()
    plt.savefig('sao_paulo_crime_density.png', dpi=300, bbox_inches='tight')
    plt.savefig('sao_paulo_crime_density.pdf', bbox_inches='tight')
    
    print("✅ Mapa guardado como sao_paulo_crime_density.png")
    
    # Mostrar mapa
    plt.show()


def create_interactive_map():
    """Crea mapa interactivo con folium"""
    
    print("\n🌐 CREANDO MAPA INTERACTIVO")
    print("=" * 30)
    
    try:
        import folium
        print("✅ Folium disponible")
        
        # Crear analizador
        analyzer = FastPostGISLike()
        
        # Cargar datos
        if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
            print("❌ Error cargando datos")
            return
        
        # Centro de São Paulo
        center_lat, center_lon = -23.5505, -46.6333
        
        # Crear mapa base
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Añadir puntos de crimen (muestra)
        points_array = np.array(analyzer.points)
        sample_size = min(1000, len(points_array))
        
        if len(points_array) > sample_size:
            indices = np.random.choice(len(points_array), sample_size, replace=False)
            sample_points = points_array[indices]
        else:
            sample_points = points_array
        
        print(f"🔴 Añadiendo {len(sample_points)} puntos al mapa...")
        
        # Añadir puntos al mapa
        for lat, lon in sample_points:
            folium.CircleMarker(
                [lat, lon],
                radius=1,
                color='red',
                fill=True,
                fillColor='red',
                fillOpacity=0.6
            ).add_to(m)
        
        # Añadir marcador del centro
        folium.Marker(
            [center_lat, center_lon],
            popup='Centro de São Paulo',
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        # Guardar mapa
        m.save('sao_paulo_crime_interactive.html')
        print("✅ Mapa interactivo guardado como sao_paulo_crime_interactive.html")
        print("💡 Abre el archivo HTML en tu navegador")
        
    except ImportError:
        print("❌ Folium no disponible, instalando...")
        import subprocess
        subprocess.run(["pip", "install", "folium"], check=True)
        print("✅ Folium instalado, ejecuta de nuevo")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 SISTEMA DE VISUALIZACIÓN DE MAPAS")
    print("=" * 40)
    
    # Intentar crear mapa con OSMnx
    create_map_with_osmnx()
    
    # Crear mapa simple como respaldo
    create_simple_map()
    
    # Crear mapa interactivo
    create_interactive_map()
    
    print("\n🎉 ¡Visualización completada!")
    print("📁 Archivos generados:")
    print("   - sao_paulo_crime_map_osmnx.png (con calles)")
    print("   - sao_paulo_crime_density.png (mapa de densidad)")
    print("   - sao_paulo_crime_interactive.html (mapa interactivo)")
