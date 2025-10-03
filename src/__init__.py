"""
Sistema de Geometría Computacional con CGAL
Optimizado para análisis rápido de datos geoespaciales
"""

from .geometry import FastPostGISLike, GeometryAnalyzer
from .data import CSVHandler, CrimeDataProcessor

__version__ = "1.0.0"
__author__ = "Pierre"

__all__ = ['FastPostGISLike', 'GeometryAnalyzer', 'CSVHandler', 'CrimeDataProcessor']