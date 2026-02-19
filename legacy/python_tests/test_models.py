"""Tests para los modelos de datos."""

import pytest
from datetime import date
from costo_personal.models import Empleado, CostoPersonal


class TestEmpleado:
    """Tests para la clase Empleado."""
    
    def test_crear_empleado_valido(self):
        """Test creación de empleado con datos válidos."""
        empleado = Empleado(
            id="E001",
            nombre="Juan Pérez",
            departamento="Tecnología",
            cargo="Desarrollador",
            salario_base=5000.0,
            fecha_ingreso=date(2020, 1, 1),
        )
        
        assert empleado.id == "E001"
        assert empleado.nombre == "Juan Pérez"
        assert empleado.departamento == "Tecnología"
        assert empleado.salario_base == 5000.0
        assert empleado.activo is True
    
    def test_empleado_salario_negativo(self):
        """Test que el salario no puede ser negativo."""
        with pytest.raises(ValueError):
            Empleado(
                id="E001",
                nombre="Juan Pérez",
                departamento="Tecnología",
                cargo="Desarrollador",
                salario_base=-1000.0,
                fecha_ingreso=date(2020, 1, 1),
            )
    
    def test_empleado_to_dict(self):
        """Test conversión de empleado a diccionario."""
        empleado = Empleado(
            id="E001",
            nombre="Juan Pérez",
            departamento="Tecnología",
            cargo="Desarrollador",
            salario_base=5000.0,
            fecha_ingreso=date(2020, 1, 1),
        )
        
        dict_empleado = empleado.to_dict()
        
        assert dict_empleado["id"] == "E001"
        assert dict_empleado["nombre"] == "Juan Pérez"
        assert dict_empleado["salario_base"] == 5000.0
        assert dict_empleado["fecha_ingreso"] == "2020-01-01"


class TestCostoPersonal:
    """Tests para la clase CostoPersonal."""
    
    def test_crear_costo_personal(self):
        """Test creación de costo personal."""
        costo = CostoPersonal(
            empleado_id="E001",
            periodo="2024-11",
            salario_base=5000.0,
            bonos=500.0,
            horas_extra=300.0,
            beneficios=200.0,
            cargas_sociales=1250.0,
            otros_costos=100.0,
        )
        
        assert costo.empleado_id == "E001"
        assert costo.periodo == "2024-11"
        assert costo.salario_base == 5000.0
    
    def test_costo_total_calculado(self):
        """Test cálculo de costo total."""
        costo = CostoPersonal(
            empleado_id="E001",
            periodo="2024-11",
            salario_base=5000.0,
            bonos=500.0,
            horas_extra=300.0,
            beneficios=200.0,
            cargas_sociales=1250.0,
            otros_costos=100.0,
        )
        
        expected_total = 5000.0 + 500.0 + 300.0 + 200.0 + 1250.0 + 100.0
        assert costo.costo_total == expected_total
    
    def test_costo_total_solo_salario_base(self):
        """Test costo total cuando solo hay salario base."""
        costo = CostoPersonal(
            empleado_id="E001",
            periodo="2024-11",
            salario_base=5000.0,
        )
        
        assert costo.costo_total == 5000.0
    
    def test_costo_personal_to_dict(self):
        """Test conversión de costo personal a diccionario."""
        costo = CostoPersonal(
            empleado_id="E001",
            periodo="2024-11",
            salario_base=5000.0,
            bonos=500.0,
        )
        
        dict_costo = costo.to_dict()
        
        assert dict_costo["empleado_id"] == "E001"
        assert dict_costo["periodo"] == "2024-11"
        assert dict_costo["salario_base"] == 5000.0
        assert dict_costo["bonos"] == 500.0
        assert "costo_total" in dict_costo
