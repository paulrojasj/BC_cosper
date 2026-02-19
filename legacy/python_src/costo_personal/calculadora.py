"""
Calculadora de costos de personal.
"""

from typing import List, Dict
from .models import Empleado, CostoPersonal


class CalculadoraCostos:
    """Calcula los costos de personal según diferentes parámetros."""
    
    def __init__(self, tasa_cargas_sociales: float = 0.25):
        """
        Inicializa la calculadora.
        
        Args:
            tasa_cargas_sociales: Porcentaje de cargas sociales sobre el salario base
        """
        self.tasa_cargas_sociales = tasa_cargas_sociales
    
    def calcular_costo_mensual(
        self,
        empleado: Empleado,
        periodo: str,
        bonos: float = 0.0,
        horas_extra: float = 0.0,
        beneficios: float = 0.0,
        otros_costos: float = 0.0,
    ) -> CostoPersonal:
        """
        Calcula el costo mensual de un empleado.
        
        Args:
            empleado: Objeto Empleado
            periodo: Periodo en formato "YYYY-MM"
            bonos: Bonos del periodo
            horas_extra: Costo de horas extra
            beneficios: Beneficios adicionales
            otros_costos: Otros costos asociados
            
        Returns:
            CostoPersonal con el desglose completo
        """
        cargas_sociales = empleado.salario_base * self.tasa_cargas_sociales
        
        return CostoPersonal(
            empleado_id=empleado.id,
            periodo=periodo,
            salario_base=empleado.salario_base,
            bonos=bonos,
            horas_extra=horas_extra,
            beneficios=beneficios,
            cargas_sociales=cargas_sociales,
            otros_costos=otros_costos,
        )
    
    def calcular_costos_departamento(
        self,
        empleados: List[Empleado],
        departamento: str,
        periodo: str,
    ) -> List[CostoPersonal]:
        """
        Calcula los costos de todos los empleados de un departamento.
        
        Args:
            empleados: Lista de empleados
            departamento: Nombre del departamento
            periodo: Periodo en formato "YYYY-MM"
            
        Returns:
            Lista de CostoPersonal para cada empleado del departamento
        """
        empleados_dept = [
            emp for emp in empleados
            if emp.departamento == departamento and emp.activo
        ]
        
        return [
            self.calcular_costo_mensual(emp, periodo)
            for emp in empleados_dept
        ]
    
    def calcular_costo_promedio_por_empleado(
        self,
        costos: List[CostoPersonal]
    ) -> float:
        """
        Calcula el costo promedio por empleado.
        
        Args:
            costos: Lista de costos de personal
            
        Returns:
            Costo promedio por empleado
        """
        if not costos:
            return 0.0
        
        total = sum(costo.costo_total for costo in costos)
        return total / len(costos)
