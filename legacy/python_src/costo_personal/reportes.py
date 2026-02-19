"""
Generador de reportes y métricas clave de costo de personal.
"""

from typing import List, Dict, Any
from collections import defaultdict
import pandas as pd
from .models import Empleado, CostoPersonal


class GeneradorReportes:
    """Genera reportes y métricas clave del proceso de costo de personal."""
    
    def __init__(self):
        """Inicializa el generador de reportes."""
        pass
    
    def generar_reporte_por_departamento(
        self,
        empleados: List[Empleado],
        costos: List[CostoPersonal],
    ) -> pd.DataFrame:
        """
        Genera un reporte de costos agrupados por departamento.
        
        Args:
            empleados: Lista de empleados
            costos: Lista de costos de personal
            
        Returns:
            DataFrame con métricas por departamento
        """
        # Crear diccionario de empleados para búsqueda rápida
        emp_dict = {emp.id: emp for emp in empleados}
        
        # Agrupar costos por departamento
        dept_data = defaultdict(lambda: {
            "cantidad_empleados": 0,
            "costo_total": 0.0,
            "salario_base_total": 0.0,
            "bonos_total": 0.0,
            "horas_extra_total": 0.0,
            "beneficios_total": 0.0,
            "cargas_sociales_total": 0.0,
        })
        
        empleados_por_dept = defaultdict(set)
        
        for costo in costos:
            empleado = emp_dict.get(costo.empleado_id)
            if empleado:
                dept = empleado.departamento
                empleados_por_dept[dept].add(costo.empleado_id)
                dept_data[dept]["costo_total"] += costo.costo_total
                dept_data[dept]["salario_base_total"] += costo.salario_base
                dept_data[dept]["bonos_total"] += costo.bonos
                dept_data[dept]["horas_extra_total"] += costo.horas_extra
                dept_data[dept]["beneficios_total"] += costo.beneficios
                dept_data[dept]["cargas_sociales_total"] += costo.cargas_sociales
        
        # Contar empleados únicos por departamento
        for dept, empleados_ids in empleados_por_dept.items():
            dept_data[dept]["cantidad_empleados"] = len(empleados_ids)
        
        # Convertir a DataFrame
        data = []
        for dept, metrics in dept_data.items():
            metrics["departamento"] = dept
            if metrics["cantidad_empleados"] > 0:
                metrics["costo_promedio_por_empleado"] = (
                    metrics["costo_total"] / metrics["cantidad_empleados"]
                )
            else:
                metrics["costo_promedio_por_empleado"] = 0.0
            data.append(metrics)
        
        df = pd.DataFrame(data)
        
        # Ordenar columnas
        columns = [
            "departamento",
            "cantidad_empleados",
            "costo_total",
            "costo_promedio_por_empleado",
            "salario_base_total",
            "bonos_total",
            "horas_extra_total",
            "beneficios_total",
            "cargas_sociales_total",
        ]
        
        return df[columns] if not df.empty else pd.DataFrame(columns=columns)
    
    def generar_metricas_clave(
        self,
        empleados: List[Empleado],
        costos: List[CostoPersonal],
    ) -> Dict[str, Any]:
        """
        Genera métricas clave del proceso de costo de personal.
        
        Args:
            empleados: Lista de empleados
            costos: Lista de costos de personal
            
        Returns:
            Diccionario con métricas clave
        """
        if not costos:
            return {
                "total_empleados": len([e for e in empleados if e.activo]),
                "costo_total": 0.0,
                "costo_promedio_por_empleado": 0.0,
                "salario_base_promedio": 0.0,
                "cargas_sociales_promedio": 0.0,
                "porcentaje_bonos": 0.0,
                "porcentaje_horas_extra": 0.0,
            }
        
        empleados_activos = [e for e in empleados if e.activo]
        
        total_costo = sum(c.costo_total for c in costos)
        total_salario_base = sum(c.salario_base for c in costos)
        total_bonos = sum(c.bonos for c in costos)
        total_horas_extra = sum(c.horas_extra for c in costos)
        total_cargas_sociales = sum(c.cargas_sociales for c in costos)
        
        num_registros = len(costos)
        
        metricas = {
            "total_empleados": len(empleados_activos),
            "costo_total": total_costo,
            "costo_promedio_por_empleado": total_costo / num_registros if num_registros > 0 else 0.0,
            "salario_base_promedio": total_salario_base / num_registros if num_registros > 0 else 0.0,
            "cargas_sociales_promedio": total_cargas_sociales / num_registros if num_registros > 0 else 0.0,
            "porcentaje_bonos": (total_bonos / total_costo * 100) if total_costo > 0 else 0.0,
            "porcentaje_horas_extra": (total_horas_extra / total_costo * 100) if total_costo > 0 else 0.0,
        }
        
        return metricas
    
    def generar_reporte_tendencia(
        self,
        costos: List[CostoPersonal],
    ) -> pd.DataFrame:
        """
        Genera un reporte de tendencia de costos por periodo.
        
        Args:
            costos: Lista de costos de personal
            
        Returns:
            DataFrame con métricas por periodo
        """
        # Agrupar por periodo
        periodo_data = defaultdict(lambda: {
            "cantidad_registros": 0,
            "costo_total": 0.0,
            "salario_base_total": 0.0,
            "bonos_total": 0.0,
            "horas_extra_total": 0.0,
        })
        
        for costo in costos:
            periodo = costo.periodo
            periodo_data[periodo]["cantidad_registros"] += 1
            periodo_data[periodo]["costo_total"] += costo.costo_total
            periodo_data[periodo]["salario_base_total"] += costo.salario_base
            periodo_data[periodo]["bonos_total"] += costo.bonos
            periodo_data[periodo]["horas_extra_total"] += costo.horas_extra
        
        # Convertir a DataFrame
        data = []
        for periodo, metrics in periodo_data.items():
            metrics["periodo"] = periodo
            if metrics["cantidad_registros"] > 0:
                metrics["costo_promedio"] = (
                    metrics["costo_total"] / metrics["cantidad_registros"]
                )
            else:
                metrics["costo_promedio"] = 0.0
            data.append(metrics)
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            df = df.sort_values("periodo")
        
        # Ordenar columnas
        columns = [
            "periodo",
            "cantidad_registros",
            "costo_total",
            "costo_promedio",
            "salario_base_total",
            "bonos_total",
            "horas_extra_total",
        ]
        
        return df[columns] if not df.empty else pd.DataFrame(columns=columns)
    
    def exportar_reporte_csv(self, df: pd.DataFrame, filename: str) -> None:
        """
        Exporta un DataFrame a un archivo CSV.
        
        Args:
            df: DataFrame a exportar
            filename: Nombre del archivo de salida
        """
        df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    def exportar_reporte_excel(self, df: pd.DataFrame, filename: str) -> None:
        """
        Exporta un DataFrame a un archivo Excel.
        
        Args:
            df: DataFrame a exportar
            filename: Nombre del archivo de salida
        """
        df.to_excel(filename, index=False, engine="openpyxl")
