"""
Ejemplo de uso del sistema de costo de personal.

Este script demuestra cómo utilizar las diferentes funcionalidades
del sistema de reportería y métricas de costo de personal.
"""

from datetime import date
from costo_personal import Empleado, CalculadoraCostos, GeneradorReportes


def ejemplo_basico():
    """Ejemplo básico de uso del sistema."""
    
    print("=" * 60)
    print("EJEMPLO: Sistema de Costo de Personal")
    print("=" * 60)
    print()
    
    # 1. Crear empleados
    print("1. Creando empleados...")
    empleados = [
        Empleado(
            id="E001",
            nombre="Juan Pérez",
            departamento="Tecnología",
            cargo="Desarrollador Senior",
            salario_base=5000.0,
            fecha_ingreso=date(2020, 1, 15),
        ),
        Empleado(
            id="E002",
            nombre="María García",
            departamento="Tecnología",
            cargo="Desarrollador Junior",
            salario_base=3000.0,
            fecha_ingreso=date(2022, 3, 1),
        ),
        Empleado(
            id="E003",
            nombre="Carlos López",
            departamento="Recursos Humanos",
            cargo="Gerente de RH",
            salario_base=6000.0,
            fecha_ingreso=date(2019, 6, 10),
        ),
        Empleado(
            id="E004",
            nombre="Ana Martínez",
            departamento="Ventas",
            cargo="Ejecutivo de Ventas",
            salario_base=4000.0,
            fecha_ingreso=date(2021, 9, 20),
        ),
    ]
    
    for emp in empleados:
        print(f"  - {emp.nombre} ({emp.cargo}) - Salario: ${emp.salario_base:,.2f}")
    print()
    
    # 2. Calcular costos mensuales
    print("2. Calculando costos mensuales (periodo 2024-11)...")
    calculadora = CalculadoraCostos(tasa_cargas_sociales=0.25)
    
    costos = []
    for emp in empleados:
        # Simular diferentes bonos y horas extra por empleado
        bonos = 500.0 if emp.departamento == "Ventas" else 200.0
        horas_extra = 300.0 if emp.cargo.startswith("Desarrollador") else 0.0
        
        costo = calculadora.calcular_costo_mensual(
            emp,
            periodo="2024-11",
            bonos=bonos,
            horas_extra=horas_extra,
            beneficios=150.0,
        )
        costos.append(costo)
        
        print(f"  - {emp.nombre}:")
        print(f"    Salario base: ${costo.salario_base:,.2f}")
        print(f"    Bonos: ${costo.bonos:,.2f}")
        print(f"    Horas extra: ${costo.horas_extra:,.2f}")
        print(f"    Cargas sociales: ${costo.cargas_sociales:,.2f}")
        print(f"    COSTO TOTAL: ${costo.costo_total:,.2f}")
        print()
    
    # 3. Generar reportes
    print("3. Generando reportes y métricas...")
    generador = GeneradorReportes()
    
    # Reporte por departamento
    print("\n   REPORTE POR DEPARTAMENTO:")
    print("   " + "-" * 56)
    df_departamento = generador.generar_reporte_por_departamento(empleados, costos)
    print(df_departamento.to_string(index=False))
    print()
    
    # Métricas clave
    print("\n   MÉTRICAS CLAVE:")
    print("   " + "-" * 56)
    metricas = generador.generar_metricas_clave(empleados, costos)
    for key, value in metricas.items():
        if isinstance(value, float):
            print(f"   {key}: ${value:,.2f}" if "porcentaje" not in key else f"   {key}: {value:.2f}%")
        else:
            print(f"   {key}: {value}")
    print()
    
    # 4. Ejemplo de tendencia (simulando múltiples periodos)
    print("4. Simulando tendencia de costos...")
    costos_tendencia = []
    
    # Agregar costos para varios periodos
    periodos = ["2024-09", "2024-10", "2024-11"]
    for periodo in periodos:
        for emp in empleados:
            costo = calculadora.calcular_costo_mensual(
                emp,
                periodo=periodo,
                bonos=200.0,
                horas_extra=100.0,
                beneficios=150.0,
            )
            costos_tendencia.append(costo)
    
    print("\n   TENDENCIA DE COSTOS:")
    print("   " + "-" * 56)
    df_tendencia = generador.generar_reporte_tendencia(costos_tendencia)
    print(df_tendencia.to_string(index=False))
    print()
    
    print("=" * 60)
    print("Ejemplo completado exitosamente!")
    print("=" * 60)


if __name__ == "__main__":
    ejemplo_basico()
