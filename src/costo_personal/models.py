"""
Modelos de datos para el sistema de costo de personal.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any


@dataclass
class Empleado:
    """Representa un empleado en el sistema."""
    
    id: str
    nombre: str
    departamento: str
    cargo: str
    salario_base: float
    fecha_ingreso: date
    activo: bool = True
    
    def __post_init__(self):
        if self.salario_base < 0:
            raise ValueError("El salario base no puede ser negativo")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el empleado a un diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "departamento": self.departamento,
            "cargo": self.cargo,
            "salario_base": self.salario_base,
            "fecha_ingreso": self.fecha_ingreso.isoformat(),
            "activo": self.activo,
        }


@dataclass
class CostoPersonal:
    """Representa el costo total de un empleado."""
    
    empleado_id: str
    periodo: str  # Formato: "YYYY-MM"
    salario_base: float
    bonos: float = 0.0
    horas_extra: float = 0.0
    beneficios: float = 0.0
    cargas_sociales: float = 0.0
    otros_costos: float = 0.0
    
    @property
    def costo_total(self) -> float:
        """Calcula el costo total del empleado para el periodo."""
        return (
            self.salario_base +
            self.bonos +
            self.horas_extra +
            self.beneficios +
            self.cargas_sociales +
            self.otros_costos
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el costo personal a un diccionario."""
        return {
            "empleado_id": self.empleado_id,
            "periodo": self.periodo,
            "salario_base": self.salario_base,
            "bonos": self.bonos,
            "horas_extra": self.horas_extra,
            "beneficios": self.beneficios,
            "cargas_sociales": self.cargas_sociales,
            "otros_costos": self.otros_costos,
            "costo_total": self.costo_total,
        }
