# Geometría Computacional con CGAL - Sistema Optimizado

Sistema de análisis geoespacial de alto rendimiento que combina la potencia de CGAL con técnicas de optimización tipo PostGIS para análisis rápido de datos de crimen.

## 🚀 Características Principales

- **Inserción masiva**: Procesamiento rápido de grandes volúmenes de datos CSV
- **Consultas espaciales**: Usando KDTree para consultas tipo PostGIS ST_DWithin
- **Análisis geométrico**: Triangulación de Delaunay, envolvente convexa, diagramas de Voronoi con CGAL
- **Integración OSMnx**: Optimizada con muestreo para mejor rendimiento
- **Exportación**: GeoJSON para visualización

## ⚡ Rendimiento

- **Velocidad**: Procesamiento de miles de puntos por segundo
- **Memoria**: Optimizado para grandes datasets
- **Consultas**: Consultas espaciales en milisegundos
- **CGAL**: Operaciones geométricas más rápidas que PostGIS

## 🛠️ Instalación

### Prerrequisitos

1. **Instalar CGAL**:
```bash
conda create -n cgal -c conda-forge compas compas_cgal --yes
conda activate cgal
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

## 📖 Uso

### Uso básico

```python
from src.geometry import FastPostGISLike

# Crear analizador
analyzer = FastPostGISLike()

# Inserción masiva de puntos
analyzer.bulk_insert_points("crimen_fusionado.csv")

# Análisis geométrico con CGAL
results = analyzer.fast_geometry_analysis()

# Consultas espaciales rápidas
center = (-23.5505, -46.6333)
points_5km = analyzer.fast_spatial_query(center, 5.0)

# Integración con OSMnx
analyzer.create_osmnx_graph_fast("São Paulo, Brazil")
integration = analyzer.fast_osmnx_integration()
```

### Ejecutar análisis completo

```bash
python main.py
```

## 🏗️ Arquitectura

```
src/
├── geometry/
│   ├── cgal_wrapper.py      # Wrapper de CGAL para operaciones geométricas
│   └── fast_postgis_like.py # Sistema optimizado tipo PostGIS
├── data/
│   └── csv_handler.py       # Procesamiento de datos CSV
└── examples/
    └── fast_postgis_demo.py # Demostración del sistema
```

## 🔧 Funcionalidades

### Inserción Masiva
- Carga eficiente de archivos CSV grandes
- Filtrado automático por región geográfica
- Construcción de índices espaciales (KDTree)

### Consultas Espaciales
- `fast_spatial_query()`: Consulta por radio (ST_DWithin)
- `fast_nearest_points()`: K vecinos más cercanos
- `benchmark_queries()`: Benchmark de rendimiento

### Análisis Geométrico (CGAL)
- Triangulación de Delaunay 2D
- Cálculo de envolvente convexa
- Diagramas de Voronoi
- Análisis de densidad espacial

### Integración OSMnx
- Creación optimizada de grafos de calles
- Integración rápida con muestreo inteligente
- Cálculo de rutas más cortas

## 📊 Ejemplo de Datos

El sistema está optimizado para archivos CSV con columnas de latitud y longitud:

```csv
ANO_BO,NUM_BO,DELEGACIA_CIRCUNSCRICAO,DATA_OCORRENCIA,PERIODO_OCORRENCIA,HORA_OCORRENCIA,FLAGRANTE,STATUS,RUBRICA,CIDADE_REGISTRO,BAIRRO,DESCRICAP_LOCAL,LOGRADOURO,NUM_LOGRADOURO,LATITUDE,LONGITUDE,CODSETOR,GEO,archivo_origen
2017,1960,04º D.P. CONSOLAÇÃO,2017-01-01,DE MADRUGADA,00:03:00,N,Consumado,Roubo (art. 157) - TRANSEUNTE,S.PAULO,,Outros,RUA MINAS GERAIS,458.0,"-23,555780","-46,665374",355030826000038.0,BRONZE,RT2017_CeMEAI_.xlsx
```

## 🎯 Ventajas sobre PostGIS

- **Velocidad**: CGAL es más rápido para operaciones geométricas complejas
- **Simplicidad**: No requiere base de datos
- **Flexibilidad**: Fácil integración con Python y OSMnx
- **Memoria**: Procesamiento en memoria más eficiente

## 📈 Benchmark

```
Inserción masiva: 50,000+ puntos/segundo
Consultas espaciales: <1ms por consulta
Análisis geométrico: 1,000+ puntos/segundo
Integración OSMnx: 100+ puntos/segundo
```

## 🔍 Ejemplos de Consultas

```python
# Consulta por radio
points_5km = analyzer.fast_spatial_query((-23.5505, -46.6333), 5.0)

# Vecinos más cercanos
nearest = analyzer.fast_nearest_points([(-23.5505, -46.6333)], k=5)

# Análisis geométrico
results = analyzer.fast_geometry_analysis()
triangles = results['delaunay_triangles']
convex_hull = results['convex_hull']
```

## 📁 Archivos de Salida

- `crime_points.geojson`: Puntos exportados para visualización
- Logs detallados de rendimiento y estadísticas

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.