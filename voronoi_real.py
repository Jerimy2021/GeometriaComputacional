#!/usr/bin/env python3
"""
Asignación REAL de puntos de crimen usando diagrama de Voronoi
Usando scipy.spatial.Voronoi para consultas espaciales eficientes
"""

import osmnx as ox
import matplotlib.pyplot as plt
import numpy as np
import time
import sys
from pathlib import Path
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial import cKDTree

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent))

from src.geometry import FastPostGISLike


def create_real_voronoi_assignment():
    """Crea asignación usando diagrama de Voronoi real"""
    
    print("🔺 SISTEMA DE ASIGNACIÓN VORONOI REAL")
    print("=" * 45)
    print("💡 Usando scipy.spatial.Voronoi para consultas espaciales")
    print("=" * 45)
    
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
    
    # Crear diagrama de Voronoi
    print("🔺 Creando diagrama de Voronoi...")
    voronoi_start = time.time()
    
    try:
        voronoi = Voronoi(node_coords)
        voronoi_time = time.time() - voronoi_start
        print(f"✅ Diagrama de Voronoi creado en {voronoi_time:.2f}s")
        print(f"   Regiones: {len(voronoi.regions)}")
        print(f"   Vértices: {len(voronoi.vertices)}")
        
    except Exception as e:
        print(f"❌ Error creando Voronoi: {e}")
        print("💡 Usando KDTree como fallback...")
        return create_kdtree_fallback(analyzer, node_coords, node_ids, G)
    
    # Asignar puntos de crimen usando Voronoi
    print("🎯 Asignando puntos de crimen usando Voronoi...")
    assignment_start = time.time()
    
    # Convertir puntos de crimen a array
    crime_points = np.array(analyzer.points)
    
    # Crear KDTree para búsquedas eficientes en Voronoi
    # (Voronoi no tiene query directo, usamos KDTree para encontrar la región)
    node_kdtree = cKDTree(node_coords)
    
    # Procesar en lotes
    batch_size = 10000
    assignments = {}
    
    for i in range(0, len(crime_points), batch_size):
        batch_end = min(i + batch_size, len(crime_points))
        batch_crime = crime_points[i:batch_end]
        
        # Encontrar nodos más cercanos usando KDTree
        distances, nearest_indices = node_kdtree.query(batch_crime, k=1)
        
        # Guardar asignaciones
        for j, (crime_point, nearest_idx, distance) in enumerate(zip(batch_crime, nearest_indices, distances)):
            global_idx = i + j
            assignments[global_idx] = {
                'crime_point': crime_point,
                'nearest_node_id': node_ids[nearest_idx],
                'distance': distance,
                'voronoi_region': nearest_idx
            }
        
        if (i // batch_size + 1) % 10 == 0:
            print(f"   Procesados {batch_end:,} de {len(crime_points):,} puntos...")
    
    assignment_time = time.time() - assignment_start
    print(f"✅ Asignación Voronoi completada en {assignment_time:.2f}s")
    
    # Estadísticas de asignación
    print(f"\n📊 ESTADÍSTICAS DE ASIGNACIÓN VORONOI:")
    print(f"   Puntos de crimen asignados: {len(assignments):,}")
    print(f"   Nodos únicos utilizados: {len(set(a['nearest_node_id'] for a in assignments.values())):,}")
    print(f"   Distancia promedio: {np.mean([a['distance'] for a in assignments.values()]):.6f} grados")
    print(f"   Distancia máxima: {np.max([a['distance'] for a in assignments.values()]):.6f} grados")
    
    # Visualizar diagrama de Voronoi
    visualize_voronoi_diagram(G, node_coords, voronoi, crime_points, assignments)
    
    # Analizar densidad por nodo
    node_crime_count = analyze_node_crime_density(assignments)
    
    # Crear mapa de calor
    create_crime_heatmap_voronoi(G, node_crime_count, voronoi)
    
    return G, crime_points, node_coords, assignments, node_crime_count, voronoi


def create_kdtree_fallback(analyzer, node_coords, node_ids, G):
    """Fallback usando KDTree si Voronoi falla"""
    
    print("🌳 Usando KDTree como método alternativo...")
    
    # Crear KDTree
    node_kdtree = cKDTree(node_coords)
    
    # Asignar puntos
    crime_points = np.array(analyzer.points)
    distances, nearest_indices = node_kdtree.query(crime_points, k=1)
    
    assignments = {}
    for i, (crime_point, nearest_idx, distance) in enumerate(zip(crime_points, nearest_indices, distances)):
        assignments[i] = {
            'crime_point': crime_point,
            'nearest_node_id': node_ids[nearest_idx],
            'distance': distance
        }
    
    print(f"✅ Asignación KDTree completada: {len(assignments):,} puntos")
    return G, crime_points, node_coords, assignments, {}, None


def visualize_voronoi_diagram(G, node_coords, voronoi, crime_points, assignments):
    """Visualiza el diagrama de Voronoi con asignaciones"""
    
    print("🎨 Creando visualización Voronoi...")
    
    # Crear figura
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    # Mapa 1: Diagrama de Voronoi
    print("🔺 Dibujando diagrama de Voronoi...")
    ox.plot_graph(
        G,
        ax=ax1,
        node_size=0,
        edge_linewidth=0.3,
        edge_color='lightblue',
        show=False,
        close=False
    )
    
    # Dibujar diagrama de Voronoi
    voronoi_plot_2d(voronoi, ax=ax1, show_vertices=False, line_colors='red', line_width=0.5)
    
    # Dibujar nodos
    ax1.scatter(
        node_coords[:, 1], node_coords[:, 0],  # lon, lat
        c='blue', s=2, alpha=0.8,
        label=f'Nodos del grafo ({len(node_coords):,})'
    )
    
    # Dibujar puntos de crimen (muestra)
    sample_size = min(5000, len(crime_points))
    if len(crime_points) > sample_size:
        sample_indices = np.random.choice(len(crime_points), sample_size, replace=False)
        sample_crime = crime_points[sample_indices]
    else:
        sample_crime = crime_points
    
    ax1.scatter(
        sample_crime[:, 1], sample_crime[:, 0],  # lon, lat
        c='red', s=0.5, alpha=0.7,
        label=f'Puntos de crimen ({len(sample_crime):,})'
    )
    
    ax1.set_title('Diagrama de Voronoi: Regiones de Influencia', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Mapa 2: Asignaciones
    print("🎯 Dibujando asignaciones...")
    ox.plot_graph(
        G,
        ax=ax2,
        node_size=0,
        edge_linewidth=0.3,
        edge_color='lightgray',
        show=False,
        close=False
    )
    
    # Dibujar nodos
    ax2.scatter(
        node_coords[:, 1], node_coords[:, 0],  # lon, lat
        c='blue', s=1, alpha=0.6,
        label=f'Nodos del grafo ({len(node_coords):,})'
    )
    
    # Dibujar asignaciones (muestra pequeña)
    sample_assignments = {k: v for k, v in list(assignments.items())[:1000]}
    
    # Crear diccionario de nodos para búsqueda rápida
    node_id_to_coords = {}
    for node_id, data in G.nodes(data=True):
        if 'y' in data and 'x' in data:
            node_id_to_coords[node_id] = [data['y'], data['x']]
    
    for i, assignment in sample_assignments.items():
        crime_point = assignment['crime_point']
        nearest_node_id = assignment['nearest_node_id']
        
        # Obtener coordenadas del nodo
        if nearest_node_id in node_id_to_coords:
            nearest_node_coord = node_id_to_coords[nearest_node_id]
            
            # Línea de asignación
            ax2.plot(
                [crime_point[1], nearest_node_coord[1]],  # lon
                [crime_point[0], nearest_node_coord[0]],  # lat
                'r-', alpha=0.4, linewidth=0.3
            )
    
    # Dibujar puntos de crimen
    ax2.scatter(
        sample_crime[:, 1], sample_crime[:, 0],  # lon, lat
        c='red', s=0.8, alpha=0.8,
        label=f'Puntos de crimen ({len(sample_crime):,})'
    )
    
    ax2.set_title('Asignaciones: Crimen → Regiones Voronoi', fontsize=14, fontweight='bold')
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
    plt.savefig('voronoi_real_diagram.png', dpi=300, bbox_inches='tight')
    plt.savefig('voronoi_real_diagram.pdf', bbox_inches='tight')
    
    print("✅ Visualización Voronoi guardada como voronoi_real_diagram.png")
    
    # Mostrar mapa
    plt.show()


def analyze_node_crime_density(assignments):
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
    
    print(f"   Nodos con crimen: {len(node_crime_count):,}")
    print(f"   Crimen promedio por nodo: {np.mean(crime_counts):.2f}")
    print(f"   Máximo crimen en un nodo: {max(crime_counts)}")
    print(f"   Nodos con 1 crimen: {sum(1 for c in crime_counts if c == 1):,}")
    print(f"   Nodos con 5+ crímenes: {sum(1 for c in crime_counts if c >= 5):,}")
    print(f"   Nodos con 10+ crímenes: {sum(1 for c in crime_counts if c >= 10):,}")
    print(f"   Nodos con 50+ crímenes: {sum(1 for c in crime_counts if c >= 50):,}")
    
    # Top 10 nodos con más crimen
    top_nodes = sorted(node_crime_count.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n🔝 TOP 10 NODOS CON MÁS CRIMEN:")
    for i, (node_id, count) in enumerate(top_nodes, 1):
        print(f"   {i:2d}. Nodo {node_id}: {count} crímenes")
    
    return node_crime_count


def create_crime_heatmap_voronoi(G, node_crime_count, voronoi):
    """Crea mapa de calor de crimen por nodo usando Voronoi"""
    
    print("\n🔥 CREANDO MAPA DE CALOR VORONOI")
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
        c=crime_counts, s=2, cmap='Reds', alpha=0.8,
        vmin=0, vmax=max(crime_counts)
    )
    
    # Añadir barra de color
    plt.colorbar(scatter, ax=ax, label='Número de crímenes')
    
    ax.set_title('Mapa de Calor Voronoi: Densidad de Crimen por Nodo', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')
    ax.grid(True, alpha=0.3)
    
    # Guardar mapa
    plt.tight_layout()
    plt.savefig('crime_heatmap_voronoi.png', dpi=300, bbox_inches='tight')
    print("✅ Mapa de calor Voronoi guardado como crime_heatmap_voronoi.png")
    
    plt.show()


if __name__ == "__main__":
    print("🔺 SISTEMA DE ASIGNACIÓN VORONOI REAL")
    print("=" * 45)
    print("💡 Usando scipy.spatial.Voronoi para consultas espaciales")
    print("💡 Cada punto asignado a su región Voronoi más cercana")
    print("=" * 45)
    
    # Crear asignaciones Voronoi reales
    G, crime_points, node_coords, assignments, node_crime_count, voronoi = create_real_voronoi_assignment()
    
    print("\n🎉 ¡Análisis Voronoi real completado!")
    print("📁 Archivos generados:")
    print("   - voronoi_real_diagram.png (diagrama de Voronoi)")
    print("   - crime_heatmap_voronoi.png (mapa de calor)")
    print("\n💡 Cada punto de crimen está asignado a su región Voronoi más cercana")
    print(f"📊 Total de asignaciones: {len(assignments):,}")
    print(f"📊 Nodos con crimen: {len(node_crime_count):,}")
    if voronoi:
        print(f"🔺 Regiones Voronoi: {len(voronoi.regions):,}")
        print(f"🔺 Vértices Voronoi: {len(voronoi.vertices):,}")
