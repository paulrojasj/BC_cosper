# Sistema de Costo de Personal

Sistema de reportería y métricas clave para el proceso de gestión de costo de personal.

## Descripción

Este proyecto proporciona herramientas para gestionar, calcular y generar reportes sobre los costos de personal de una organización. Permite:

- Gestión de empleados y sus datos básicos
- Cálculo automático de costos mensuales (salario base, bonos, horas extra, cargas sociales, etc.)
- Generación de reportes por departamento
- Métricas clave del proceso de costo de personal
- Análisis de tendencias de costos por periodo

## Características

- **Modelos de Datos**: Clases para representar empleados y costos de personal
- **Calculadora de Costos**: Motor de cálculo con soporte para múltiples conceptos (bonos, horas extra, cargas sociales)
- **Generador de Reportes**: Creación de reportes en diferentes formatos (DataFrames de pandas)
- **Métricas Clave**: Cálculo automático de indicadores importantes
- **Análisis de Tendencias**: Seguimiento de costos a lo largo del tiempo

## Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip

### Instalación desde el código fuente

```bash
# Clonar el repositorio
git clone https://github.com/paulrojasj/costo_personal.git
cd costo_personal

# Instalar dependencias
pip install -r requirements.txt

# Instalar el paquete
pip install -e .
```

### Instalación para desarrollo

```bash
# Instalar con dependencias de desarrollo
pip install -e ".[dev]"
```

## Uso

### Ejemplo Básico

```python
from datetime import date
from costo_personal import Empleado, CalculadoraCostos, GeneradorReportes

# Crear un empleado
empleado = Empleado(
    id="E001",
    nombre="Juan Pérez",
    departamento="Tecnología",
    cargo="Desarrollador Senior",
    salario_base=5000.0,
    fecha_ingreso=date(2020, 1, 15),
)

# Calcular costo mensual
calculadora = CalculadoraCostos(tasa_cargas_sociales=0.25)
costo = calculadora.calcular_costo_mensual(
    empleado,
    periodo="2024-11",
    bonos=500.0,
    horas_extra=300.0,
    beneficios=150.0,
)

print(f"Costo total: ${costo.costo_total:,.2f}")
```

### Generar Reportes

```python
# Generar reporte por departamento
generador = GeneradorReportes()
df_departamento = generador.generar_reporte_por_departamento(empleados, costos)
print(df_departamento)

# Obtener métricas clave
metricas = generador.generar_metricas_clave(empleados, costos)
print(f"Costo total: ${metricas['costo_total']:,.2f}")
print(f"Costo promedio por empleado: ${metricas['costo_promedio_por_empleado']:,.2f}")
```

### Ejemplo Completo

Consulta el archivo `examples/ejemplo_uso.py` para un ejemplo completo de uso del sistema.

```bash
python examples/ejemplo_uso.py
```

## Estructura del Proyecto

```
costo_personal/
├── src/
│   └── costo_personal/
│       ├── __init__.py
│       ├── models.py           # Modelos de datos
│       ├── calculadora.py      # Motor de cálculo de costos
│       └── reportes.py         # Generador de reportes y métricas
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_calculadora.py
│   └── test_reportes.py
├── examples/
│   └── ejemplo_uso.py
├── requirements.txt
├── setup.py
└── README.md
```

## Desarrollo

### Ejecutar Tests

```bash
pytest tests/
```

### Ejecutar Tests con Cobertura

```bash
pytest --cov=costo_personal tests/
```

## Métricas Disponibles

El sistema proporciona las siguientes métricas clave:

- **Total de Empleados**: Cantidad de empleados activos
- **Costo Total**: Suma de todos los costos del periodo
- **Costo Promedio por Empleado**: Costo total dividido por número de empleados
- **Salario Base Promedio**: Promedio de salarios base
- **Cargas Sociales Promedio**: Promedio de cargas sociales
- **Porcentaje de Bonos**: Proporción de bonos sobre el costo total
- **Porcentaje de Horas Extra**: Proporción de horas extra sobre el costo total

## Reportes Disponibles

1. **Reporte por Departamento**: Agrupa costos y métricas por departamento
2. **Reporte de Tendencia**: Muestra la evolución de costos a lo largo del tiempo
3. **Métricas Clave**: Resumen ejecutivo de los indicadores principales

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## Autor

Paul Rojas

## Soporte

Para preguntas o problemas, por favor abre un issue en el repositorio de GitHub.
