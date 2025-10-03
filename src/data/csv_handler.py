"""
Manejador de datos CSV para puntos geoespaciales
Implementa el patrón Strategy para diferentes tipos de procesamiento de datos
"""

import pandas as pd
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class DataProcessor(ABC):
    """Interfaz abstracta para procesadores de datos"""
    
    @abstractmethod
    def process(self, data: pd.DataFrame) -> List[Tuple[float, float]]:
        """Procesa los datos y retorna una lista de coordenadas (lat, lon)"""
        pass


class CrimeDataProcessor(DataProcessor):
    """Procesador específico para datos de crimen con latitud y longitud"""
    
    def __init__(self, lat_col: str = "LATITUDE", lon_col: str = "LONGITUDE"):
        self.lat_col = lat_col
        self.lon_col = lon_col
    
    def process(self, data: pd.DataFrame) -> List[Tuple[float, float]]:
        """Procesa datos de crimen y extrae coordenadas válidas"""
        try:
            # Filtrar filas con coordenadas válidas
            valid_data = data.dropna(subset=[self.lat_col, self.lon_col])
            
            # Convertir coordenadas a float, manejando formato brasileño
            valid_data[self.lat_col] = valid_data[self.lat_col].astype(str).str.replace(',', '.').astype(float)
            valid_data[self.lon_col] = valid_data[self.lon_col].astype(str).str.replace(',', '.').astype(float)
            
            # Filtrar coordenadas válidas (São Paulo está aproximadamente entre -24 y -23 lat, -47 y -46 lon)
            valid_data = valid_data[
                (valid_data[self.lat_col] >= -24.0) & (valid_data[self.lat_col] <= -23.0) &
                (valid_data[self.lon_col] >= -47.0) & (valid_data[self.lon_col] <= -46.0)
            ]
            
            coordinates = list(zip(valid_data[self.lat_col], valid_data[self.lon_col]))
            logger.info(f"Procesados {len(coordinates)} puntos válidos de {len(data)} registros")
            
            return coordinates
            
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
            return []


class CSVHandler:
    """Manejador principal para archivos CSV con patrón Strategy"""
    
    def __init__(self, processor: DataProcessor):
        self.processor = processor
        self.data: Optional[pd.DataFrame] = None
        self.coordinates: List[Tuple[float, float]] = []
    
    def load_csv(self, file_path: str) -> bool:
        """Carga un archivo CSV"""
        try:
            self.data = pd.read_csv(file_path)
            logger.info(f"CSV cargado exitosamente: {len(self.data)} registros")
            return True
        except Exception as e:
            logger.error(f"Error cargando CSV: {e}")
            return False
    
    def process_data(self) -> List[Tuple[float, float]]:
        """Procesa los datos usando el procesador configurado"""
        if self.data is None:
            logger.warning("No hay datos cargados")
            return []
        
        self.coordinates = self.processor.process(self.data)
        return self.coordinates
    
    def get_coordinates(self) -> List[Tuple[float, float]]:
        """Retorna las coordenadas procesadas"""
        return self.coordinates
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """Retorna el DataFrame original"""
        return self.data
