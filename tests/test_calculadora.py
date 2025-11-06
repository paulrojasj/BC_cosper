"""Tests para el calculador de costos."""

import pytest
from datetime import date
from costo_personal.models import Empleado
from costo_personal.calculadora import CalculadoraCostos


class TestCalculadoraCostos:
    """Tests para la clase CalculadoraCostos."""
    
    def test_calcular_costo_mensual_basico(self):
        """Test cálculo de costo mensual básico."""
        empleado = Empleado(
            id="E001",
            nombre="Juan Pérez",
            departamento="Tecnología",
            cargo="Desarrollador",
            salario_base=5000.0,
            fecha_ingreso=date(2020, 1, 1),
        )
        
        calculadora = CalculadoraCostos(tasa_cargas_sociales=0.25)
        costo = calculadora.calcular_costo_mensual(empleado, "2024-11")
        
        assert costo.empleado_id == "E001"
        assert costo.periodo == "2024-11"
        assert costo.salario_base == 5000.0
        assert costo.cargas_sociales == 1250.0  # 25% de 5000
        assert costo.costo_total == 6250.0
    
    def test_calcular_costo_mensual_con_extras(self):
        """Test cálculo de costo mensual con bonos y horas extra."""
        empleado = Empleado(
            id="E001",
            nombre="Juan Pérez",
            departamento="Tecnología",
            cargo="Desarrollador",
            salario_base=5000.0,
            fecha_ingreso=date(2020, 1, 1),
        )
        
        calculadora = CalculadoraCostos(tasa_cargas_sociales=0.20)
        costo = calculadora.calcular_costo_mensual(
            empleado,
            "2024-11",
            bonos=500.0,
            horas_extra=300.0,
            beneficios=200.0,
            otros_costos=100.0,
        )
        
        assert costo.bonos == 500.0
        assert costo.horas_extra == 300.0
        assert costo.beneficios == 200.0
        assert costo.otros_costos == 100.0
        assert costo.cargas_sociales == 1000.0  # 20% de 5000
        expected_total = 5000.0 + 500.0 + 300.0 + 200.0 + 1000.0 + 100.0
        assert costo.costo_total == expected_total
    
    def test_calcular_costos_departamento(self):
        """Test cálculo de costos por departamento."""
        empleados = [
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
        
        calculadora = CalculadoraCostos(tasa_cargas_sociales=0.25)
        costos = calculadora.calcular_costos_departamento(
            empleados,
            "Tecnología",
            "2024-11"
        )
        
        assert len(costos) == 2
        assert all(c.periodo == "2024-11" for c in costos)
        empleados_ids = {c.empleado_id for c in costos}
        assert "E001" in empleados_ids
        assert "E002" in empleados_ids
        assert "E003" not in empleados_ids
    
    def test_calcular_costos_departamento_solo_activos(self):
        """Test que solo calcula costos para empleados activos."""
        empleados = [
            Empleado(
                id="E001",
                nombre="Juan Pérez",
                departamento="Tecnología",
                cargo="Desarrollador",
                salario_base=5000.0,
                fecha_ingreso=date(2020, 1, 1),
                activo=True,
            ),
            Empleado(
                id="E002",
                nombre="María García",
                departamento="Tecnología",
                cargo="Tester",
                salario_base=3000.0,
                fecha_ingreso=date(2021, 1, 1),
                activo=False,
            ),
        ]
        
        calculadora = CalculadoraCostos()
        costos = calculadora.calcular_costos_departamento(
            empleados,
            "Tecnología",
            "2024-11"
        )
        
        assert len(costos) == 1
        assert costos[0].empleado_id == "E001"
    
    def test_calcular_costo_promedio_por_empleado(self):
        """Test cálculo de costo promedio por empleado."""
        empleado = Empleado(
            id="E001",
            nombre="Juan Pérez",
            departamento="Tecnología",
            cargo="Desarrollador",
            salario_base=5000.0,
            fecha_ingreso=date(2020, 1, 1),
        )
        
        calculadora = CalculadoraCostos(tasa_cargas_sociales=0.25)
        
        costos = [
            calculadora.calcular_costo_mensual(empleado, "2024-11"),
        ]
        
        promedio = calculadora.calcular_costo_promedio_por_empleado(costos)
        assert promedio == 6250.0
    
    def test_calcular_costo_promedio_lista_vacia(self):
        """Test cálculo de promedio con lista vacía."""
        calculadora = CalculadoraCostos()
        promedio = calculadora.calcular_costo_promedio_por_empleado([])
        assert promedio == 0.0
