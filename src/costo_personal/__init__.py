"""
Sistema de reportería y métricas de costo de personal.

Este paquete proporciona herramientas para gestionar, calcular y reportar
los costos de personal de una organización.
"""

__version__ = "0.1.0"

from .models import Empleado, CostoPersonal
from .calculadora import CalculadoraCostos
from .reportes import GeneradorReportes

__all__ = [
    "Empleado",
    "CostoPersonal",
    "CalculadoraCostos",
    "GeneradorReportes",
]
