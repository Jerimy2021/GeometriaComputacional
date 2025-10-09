#!/usr/bin/env python3
"""
Asignación de puntos de crimen a nodos más cercanos usando diagrama de Voronoi
"""

import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import time
import random
import sys
from pathlib import Path
from scipy.spatial import Voronoi
from scipy.spatial.distance import cdist

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent))

from src.geometry import FastPostGISLike


def create_voronoi_assignment():
    """Crea asignación de puntos de crimen a nodos usando Voronoi"""
    
    print("🗺️  ASIGNACIÓN VORONOI DE PUNTOS DE CRIMEN A NODOS")
    print("=" * 55)
    
    # Crear analizador
    analyzer = FastPostGISLike()
    
    # Cargar datos de crimen
    print("📊 Cargando datos de crimen...")
    if not analyzer.bulk_insert_points("/Users/pierre/Downloads/crimen_fusionado.csv"):
        print("❌ Error cargando datos")
        return
    
    print(f"✅ {len(analyzer.points)} puntos de crimen cargados")
    
    # Crear grafo OSMnx
    print("🗺️  Creando grafo de São Paulo...")
    start_time = time.time()
    
    try:
        G = ox.graph_from_place('São Paulo, Brazil', network_type='drive', simplify=True)
        graph_time = time.time() - start_time
        print(f"✅ Grafo creado en {graph_time:.2f}s: {len(G.nodes)} nodos, {len(G.edges)} aristas")
        
    except Exception as e:
        print(f"❌ Error creando grafo: {e}")
        return
    
    # Extraer coordenadas de nodos del grafo
    print("📍 Extrayendo coordenadas de nodos...")
    node_coords = []
    node_ids = []
    
    for node_id, data in G.nodes(data=True):
        if 'y' in data and 'x' in data:  # lat, lon
            lat, lon = data['y'], data['x']
            node_coords.append([lat, lon])
            node_ids.append(node_id)
    
    node_coords = np.array(node_coords)
    print(f"✅ {len(node_coords)} nodos extraídos del grafo")
    
    # Crear diagrama de Voronoi usando los nodos como centros
    print("🔺 Creando diagrama de Voronoi...")
    voronoi_start = time.time()
    
    try:
        # Usar scipy para Voronoi (más estable que CGAL para este caso)
        vor = Voronoi(node_coords)
        voronoi_time = time.time() - voronoi_start
        print(f"✅ Diagrama de Voronoi creado en {voronoi_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error creando Voronoi: {e}")
        return
    
    # Asignar puntos de crimen a nodos más cercanos
    print("🎯 Asignando puntos de crimen a nodos más cercanos...")
    assignment_start = time.time()
    
    # Convertir puntos de crimen a array
    crime_points = np.array(analyzer.points)
    
    # Calcular distancias a todos los nodos
    distances = cdist(crime_points, node_coords)
    
    # Encontrar nodo más cercano para cada punto de crimen
    nearest_node_indices = np.argmin(distances, axis=1)
    nearest_node_ids = [node_ids[i] for i in nearest_node_indices]
    
    assignment_time = time.time() - assignment_start
    print(f"✅ Asignación completada en {assignment_time:.2f}s")
    
    # Crear diccionario de asignaciones
    assignments = {}
    for i, (crime_point, nearest_node_id) in enumerate(zip(crime_points, nearest_node_ids)):
        assignments[i] = {
            'crime_point': crime_point,
            'nearest_node_id': nearest_node_id,
            'distance': distances[i, nearest_node_indices[i]]
        }
    
    # Estadísticas de asignación
    print(f"\n📊 ESTADÍSTICAS DE ASIGNACIÓN:")
    print(f"   Puntos de crimen asignados: {len(assignments)}")
    print(f"   Nodos únicos utilizados: {len(set(nearest_node_ids))}")
    print(f"   Distancia promedio: {np.mean([a['distance'] for a in assignments.values()]):.6f} grados")
    print(f"   Distancia máxima: {np.max([a['distance'] for a in assignments.values()]):.6f} grados")
    
    # Visualizar asignaciones
    visualize_voronoi_assignment(G, crime_points, node_coords, nearest_node_indices, assignments)
    
    return G, crime_points, node_coords, assignments


def visualize_voronoi_assignment(G, crime_points, node_coords, nearest_node_indices, assignments):
    """Visualiza las asignaciones Voronoi"""
    
    print("🎨 Creando visualización...")
    
    # Crear figura
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    # Mapa 1: Grafo con puntos de crimen
    print("🛣️  Dibujando grafo con puntos de crimen...")
    ox.plot_graph(
        G,
        ax=ax1,
        node_size=0,
        edge_linewidth=0.3,
        edge_color='lightblue',
        show=False,
        close=False
    )
    
    # Dibujar puntos de crimen (muestra)
    sample_size = min(5000, len(crime_points))
    if len(crime_points) > sample_size:
        sample_indices = np.random.choice(len(crime_points), sample_size, replace=False)
        sample_crime = crime_points[sample_indices]
    else:
        sample_crime = crime_points
        sample_indices = np.arange(len(crime_points))
    
    ax1.scatter(
        sample_crime[:, 1], sample_crime[:, 0],  # lon, lat
        c='red', s=0.5, alpha=0.7,
        label=f'Puntos de crimen ({len(sample_crime)})'
    )
    
    ax1.set_title('Grafo de Calles con Puntos de Crimen', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Mapa 2: Asignaciones Voronoi
    print("🔺 Dibujando asignaciones Voronoi...")
    ox.plot_graph(
        G,
        ax=ax2,
        node_size=0,
        edge_linewidth=0.3,
        edge_color='lightgray',
        show=False,
        close=False
    )
    
    # Dibujar nodos del grafo
    ax2.scatter(
        node_coords[:, 1], node_coords[:, 0],  # lon, lat
        c='blue', s=2, alpha=0.8,
        label=f'Nodos del grafo ({len(node_coords)})'
    )
    
    # Dibujar asignaciones (muestra)
    sample_assignments = {k: v for k, v in list(assignments.items())[:sample_size]}
    
    for i, assignment in sample_assignments.items():
        crime_point = assignment['crime_point']
        nearest_node_idx = nearest_node_indices[i]
        nearest_node_coord = node_coords[nearest_node_idx]
        
        # Línea de asignación
        ax2.plot(
            [crime_point[1], nearest_node_coord[1]],  # lon
            [crime_point[0], nearest_node_coord[0]],  # lat
            'r-', alpha=0.3, linewidth=0.5
        )
    
    # Dibujar puntos de crimen
    ax2.scatter(
        sample_crime[:, 1], sample_crime[:, 0],  # lon, lat
        c='red', s=1, alpha=0.8,
        label=f'Puntos de crimen ({len(sample_crime)})'
    )
    
    ax2.set_title('Asignaciones Voronoi: Crimen → Nodos Más Cercanos', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Ajustar límites
    all_lats = np.concatenate([crime_points[:, 0], node_coords[:, 0]])
    all_lons = np.concatenate([crime_points[:, 1], node_coords[:, 1]])
    
    margin = 0.005
    for ax in [ax1, ax2]:
        ax.set_xlim(all_lons.min() - margin, all_lons.max() + margin)
        ax.set_ylim(all_lats.min() - margin, all_lats.max() + margin)
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
    
    # Guardar visualización
    plt.tight_layout()
    plt.savefig('voronoi_crime_assignment.png', dpi=300, bbox_inches='tight')
    plt.savefig('voronoi_crime_assignment.pdf', bbox_inches='tight')
    
    print("✅ Visualización guardada como voronoi_crime_assignment.png")
    
    # Mostrar mapa
    plt.show()


def analyze_node_crime_density(G, assignments):
    """Analiza la densidad de crimen por nodo"""
    
    print("\n📊 ANÁLISIS DE DENSIDAD DE CRIMEN POR NODO")
    print("=" * 45)
    
    # Contar crimen por nodo
    node_crime_count = {}
    for assignment in assignments.values():
        node_id = assignment['nearest_node_id']
        node_crime_count[node_id] = node_crime_count.get(node_id, 0) + 1
    
    # Estadísticas
    crime_counts = list(node_crime_count.values())
    
    print(f"   Nodos con crimen: {len(node_crime_count)}")
    print(f"   Crimen promedio por nodo: {np.mean(crime_counts):.2f}")
    print(f"   Máximo crimen en un nodo: {max(crime_counts)}")
    print(f"   Nodos con 1 crimen: {sum(1 for c in crime_counts if c == 1)}")
    print(f"   Nodos con 5+ crímenes: {sum(1 for c in crime_counts if c >= 5)}")
    print(f"   Nodos con 10+ crímenes: {sum(1 for c in crime_counts if c >= 10)}")
    
    # Top 10 nodos con más crimen
    top_nodes = sorted(node_crime_count.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n🔝 TOP 10 NODOS CON MÁS CRIMEN:")
    for i, (node_id, count) in enumerate(top_nodes, 1):
        print(f"   {i:2d}. Nodo {node_id}: {count} crímenes")
    
    return node_crime_count


def create_crime_heatmap(G, node_crime_count):
    """Crea mapa de calor de crimen por nodo"""
    
    print("\n🔥 CREANDO MAPA DE CALOR DE CRIMEN")
    print("=" * 35)
    
    # Crear figura
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Dibujar grafo
    ox.plot_graph(
        G,
        ax=ax,
        node_size=0,
        edge_linewidth=0.3,
        edge_color='lightgray',
        show=False,
        close=False
    )
    
    # Preparar datos para mapa de calor
    node_coords = []
    crime_counts = []
    
    for node_id, data in G.nodes(data=True):
        if 'y' in data and 'x' in data:
            lat, lon = data['y'], data['x']
            node_coords.append([lat, lon])
            crime_counts.append(node_crime_count.get(node_id, 0))
    
    node_coords = np.array(node_coords)
    crime_counts = np.array(crime_counts)
    
    # Crear mapa de calor
    scatter = ax.scatter(
        node_coords[:, 1], node_coords[:, 0],  # lon, lat
        c=crime_counts, s=3, cmap='Reds', alpha=0.8,
        vmin=0, vmax=max(crime_counts)
    )
    
    # Añadir barra de color
    plt.colorbar(scatter, ax=ax, label='Número de crímenes')
    
    ax.set_title('Mapa de Calor: Densidad de Crimen por Nodo', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')
    ax.grid(True, alpha=0.3)
    
    # Guardar mapa
    plt.tight_layout()
    plt.savefig('crime_heatmap_by_node.png', dpi=300, bbox_inches='tight')
    print("✅ Mapa de calor guardado como crime_heatmap_by_node.png")
    
    plt.show()


if __name__ == "__main__":
    print("🚀 SISTEMA DE ASIGNACIÓN VORONOI")
    print("=" * 40)
    
    # Crear asignaciones Voronoi
    G, crime_points, node_coords, assignments = create_voronoi_assignment()
    
    # Analizar densidad por nodo
    node_crime_count = analyze_node_crime_density(G, assignments)
    
    # Crear mapa de calor
    create_crime_heatmap(G, node_crime_count)
    
    print("\n🎉 ¡Análisis Voronoi completado!")
    print("📁 Archivos generados:")
    print("   - voronoi_crime_assignment.png (asignaciones)")
    print("   - crime_heatmap_by_node.png (mapa de calor)")
    print("\n💡 Cada punto de crimen está asignado al nodo (esquina) más cercano")
    print("   usando diagrama de Voronoi basado en la red de calles de São Paulo")
