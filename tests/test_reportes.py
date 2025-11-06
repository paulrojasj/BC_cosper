"""Tests para el generador de reportes."""

import pytest
from datetime import date
from costo_personal.models import Empleado, CostoPersonal
from costo_personal.reportes import GeneradorReportes


class TestGeneradorReportes:
    """Tests para la clase GeneradorReportes."""
    
    @pytest.fixture
    def empleados_ejemplo(self):
        """Fixture con empleados de ejemplo."""
        return [
            Empleado(
                id="E001",
                nombre="Juan Pérez",
                departamento="Tecnología",
                cargo="Desarrollador",
                salario_base=5000.0,
                fecha_ingreso=date(2020, 1, 1),
            ),
            Empleado(
                id="E002",
                nombre="María García",
                departamento="Tecnología",
                cargo="Tester",
                salario_base=3000.0,
                fecha_ingreso=date(2021, 1, 1),
            ),
            Empleado(
                id="E003",
                nombre="Carlos López",
                departamento="Ventas",
                cargo="Vendedor",
                salario_base=4000.0,
                fecha_ingreso=date(2022, 1, 1),
            ),
        ]
    
    @pytest.fixture
    def costos_ejemplo(self):
        """Fixture con costos de ejemplo."""
        return [
            CostoPersonal(
                empleado_id="E001",
                periodo="2024-11",
                salario_base=5000.0,
                bonos=500.0,
                horas_extra=300.0,
                beneficios=200.0,
                cargas_sociales=1250.0,
            ),
            CostoPersonal(
                empleado_id="E002",
                periodo="2024-11",
                salario_base=3000.0,
                bonos=200.0,
                horas_extra=100.0,
                beneficios=200.0,
                cargas_sociales=750.0,
            ),
            CostoPersonal(
                empleado_id="E003",
                periodo="2024-11",
                salario_base=4000.0,
                bonos=800.0,
                horas_extra=0.0,
                beneficios=200.0,
                cargas_sociales=1000.0,
            ),
        ]
    
    def test_generar_reporte_por_departamento(self, empleados_ejemplo, costos_ejemplo):
        """Test generación de reporte por departamento."""
        generador = GeneradorReportes()
        df = generador.generar_reporte_por_departamento(empleados_ejemplo, costos_ejemplo)
        
        assert not df.empty
        assert len(df) == 2  # Tecnología y Ventas
        
        # Verificar que las columnas esperadas existen
        expected_columns = [
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
        for col in expected_columns:
            assert col in df.columns
        
        # Verificar datos del departamento de Tecnología
        tech_row = df[df["departamento"] == "Tecnología"].iloc[0]
        assert tech_row["cantidad_empleados"] == 2
        assert tech_row["salario_base_total"] == 8000.0  # 5000 + 3000
        assert tech_row["bonos_total"] == 700.0  # 500 + 200
    
    def test_generar_metricas_clave(self, empleados_ejemplo, costos_ejemplo):
        """Test generación de métricas clave."""
        generador = GeneradorReportes()
        metricas = generador.generar_metricas_clave(empleados_ejemplo, costos_ejemplo)
        
        assert metricas["total_empleados"] == 3
        assert metricas["costo_total"] > 0
        assert metricas["costo_promedio_por_empleado"] > 0
        assert metricas["salario_base_promedio"] == 4000.0  # (5000+3000+4000)/3
        assert "porcentaje_bonos" in metricas
        assert "porcentaje_horas_extra" in metricas
    
    def test_generar_metricas_clave_sin_costos(self, empleados_ejemplo):
        """Test generación de métricas cuando no hay costos."""
        generador = GeneradorReportes()
        metricas = generador.generar_metricas_clave(empleados_ejemplo, [])
        
        assert metricas["total_empleados"] == 3
        assert metricas["costo_total"] == 0.0
        assert metricas["costo_promedio_por_empleado"] == 0.0
    
    def test_generar_reporte_tendencia(self):
        """Test generación de reporte de tendencia."""
        costos = [
            CostoPersonal(
                empleado_id="E001",
                periodo="2024-09",
                salario_base=5000.0,
                cargas_sociales=1250.0,
            ),
            CostoPersonal(
                empleado_id="E001",
                periodo="2024-10",
                salario_base=5000.0,
                cargas_sociales=1250.0,
            ),
            CostoPersonal(
                empleado_id="E001",
                periodo="2024-11",
                salario_base=5000.0,
                bonos=500.0,
                cargas_sociales=1250.0,
            ),
        ]
        
        generador = GeneradorReportes()
        df = generador.generar_reporte_tendencia(costos)
        
        assert not df.empty
        assert len(df) == 3
        
        # Verificar que está ordenado por periodo
        periodos = df["periodo"].tolist()
        assert periodos == ["2024-09", "2024-10", "2024-11"]
        
        # Verificar columnas
        expected_columns = [
            "periodo",
            "cantidad_registros",
            "costo_total",
            "costo_promedio",
            "salario_base_total",
            "bonos_total",
            "horas_extra_total",
        ]
        for col in expected_columns:
            assert col in df.columns
    
    def test_generar_reporte_tendencia_vacio(self):
        """Test generación de reporte de tendencia con lista vacía."""
        generador = GeneradorReportes()
        df = generador.generar_reporte_tendencia([])
        
        assert df.empty
        # Debe tener las columnas esperadas aunque esté vacío
        expected_columns = [
            "periodo",
            "cantidad_registros",
            "costo_total",
            "costo_promedio",
            "salario_base_total",
            "bonos_total",
            "horas_extra_total",
        ]
        for col in expected_columns:
            assert col in df.columns
