#!/usr/bin/env python3
"""
Visualización rápida del mapa de São Paulo con puntos de crimen
Basado en el código que funciona correctamente
"""

import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import time
import random
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent))

from src.geometry import FastPostGISLike


def create_quick_map():
    """Crea mapa rápido usando el código que funciona"""
    
    print("🗺️  CREANDO MAPA RÁPIDO DE SÃO PAULO")
    print("=" * 45)
    
    # Crear analizador
    analyzer = FastPostGISLike()
    
    # Cargar datos
    print("📊 Cargando datos de crimen...")
    if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
        print("❌ Error cargando datos")
        return
    
    print(f"✅ {len(analyzer.points)} puntos cargados")
    
    # Crear grafo OSMnx (usando tu código que funciona)
    print("🗺️  Creando grafo de São Paulo...")
    start_time = time.time()
    
    try:
        G = ox.graph_from_place('São Paulo, Brazil', network_type='drive', simplify=True)
        graph_time = time.time() - start_time
        print(f"✅ Grafo creado en {graph_time:.2f}s: {len(G.nodes)} nodos, {len(G.edges)} aristas")
        
    except Exception as e:
        print(f"❌ Error creando grafo: {e}")
        return
    
    # Preparar datos de crimen
    points_array = np.array(analyzer.points)
    lats = points_array[:, 0]
    lons = points_array[:, 1]
    
    # Usar muestra para mejor rendimiento
    sample_size = min(30000, len(points_array))
    if len(points_array) > sample_size:
        indices = np.random.choice(len(points_array), sample_size, replace=False)
        sample_lats = lats[indices]
        sample_lons = lons[indices]
    else:
        sample_lats = lats
        sample_lons = lons
    
    print(f"🔴 Visualizando {len(sample_lats)} puntos de crimen")
    
    # Crear figura
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    
    # Dibujar grafo de calles
    print("🛣️  Dibujando calles...")
    ox.plot_graph(
        G,
        ax=ax,
        node_size=0,
        edge_linewidth=0.4,
        edge_color='lightblue',
        show=False,
        close=False
    )
    
    # Dibujar puntos de crimen
    print("🔴 Dibujando puntos de crimen...")
    ax.scatter(
        sample_lons, sample_lats,
        c='red', s=0.8, alpha=0.7,
        label=f'Puntos de crimen ({len(sample_lats):,})'
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
    plt.savefig('sao_paulo_crime_map_quick.png', dpi=300, bbox_inches='tight')
    plt.savefig('sao_paulo_crime_map_quick.pdf', bbox_inches='tight')
    
    print("✅ Mapa guardado como sao_paulo_crime_map_quick.png")
    
    # Mostrar mapa
    plt.show()
    
    return G, sample_lats, sample_lons


def create_density_map():
    """Crea mapa de densidad de crimen"""
    
    print("\n🔥 CREANDO MAPA DE DENSIDAD")
    print("=" * 30)
    
    # Crear analizador
    analyzer = FastPostGISLike()
    
    # Cargar datos
    if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
        return
    
    # Preparar datos
    points_array = np.array(analyzer.points)
    lats = points_array[:, 0]
    lons = points_array[:, 1]
    
    # Crear figura
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Crear mapa de calor
    print("🔥 Creando mapa de densidad...")
    hb = ax.hexbin(lons, lats, gridsize=60, cmap='Reds', alpha=0.8)
    
    # Añadir barra de color
    plt.colorbar(hb, ax=ax, label='Densidad de crimen')
    
    # Configurar mapa
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    ax.set_title('Mapa de Densidad de Crimen - São Paulo', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Guardar mapa
    plt.tight_layout()
    plt.savefig('sao_paulo_crime_density.png', dpi=300, bbox_inches='tight')
    print("✅ Mapa de densidad guardado como sao_paulo_crime_density.png")
    
    plt.show()


def create_interactive_map():
    """Crea mapa interactivo con folium"""
    
    print("\n🌐 CREANDO MAPA INTERACTIVO")
    print("=" * 30)
    
    try:
        import folium
        
        # Crear analizador
        analyzer = FastPostGISLike()
        
        # Cargar datos
        if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
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
        sample_size = min(2000, len(points_array))
        
        if len(points_array) > sample_size:
            indices = np.random.choice(len(points_array), sample_size, replace=False)
            sample_points = points_array[indices]
        else:
            sample_points = points_array
        
        print(f"🔴 Añadiendo {len(sample_points)} puntos al mapa interactivo...")
        
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
        print("❌ Folium no disponible")
    except Exception as e:
        print(f"❌ Error: {e}")


def analyze_crime_patterns():
    """Analiza patrones de crimen"""
    
    print("\n📊 ANÁLISIS DE PATRONES DE CRIMEN")
    print("=" * 40)
    
    # Crear analizador
    analyzer = FastPostGISLike()
    
    # Cargar datos
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
    total_points = len(analyzer.points)
    
    for region, (lat, lon, radius) in regions.items():
        points = analyzer.fast_spatial_query((lat, lon), radius)
        percentage = (len(points) / total_points) * 100
        print(f"   {region}: {len(points):,} puntos ({percentage:.1f}%)")
    
    # Análisis de densidad
    print(f"\n📈 Estadísticas generales:")
    print(f"   Total de puntos: {total_points:,}")
    print(f"   Región con más crimen: {max(regions.keys(), key=lambda r: len(analyzer.fast_spatial_query(regions[r][:2], regions[r][2])))}")


if __name__ == "__main__":
    print("🚀 SISTEMA DE VISUALIZACIÓN RÁPIDO")
    print("=" * 40)
    
    # Crear mapa principal
    G, sample_lats, sample_lons = create_quick_map()
    
    # Crear mapa de densidad
    create_density_map()
    
    # Crear mapa interactivo
    create_interactive_map()
    
    # Análisis de patrones
    analyze_crime_patterns()
    
    print("\n🎉 ¡Visualización completada!")
    print("📁 Archivos generados:")
    print("   - sao_paulo_crime_map_quick.png (mapa con calles)")
    print("   - sao_paulo_crime_density.png (mapa de densidad)")
    print("   - sao_paulo_crime_interactive.html (mapa interactivo)")
