"""
Módulo de geometría computacional optimizado
"""

from .cgal_wrapper import CGALWrapper, GeometryAnalyzer
from .fast_postgis_like import FastPostGISLike

__all__ = ['CGALWrapper', 'GeometryAnalyzer', 'FastPostGISLike']