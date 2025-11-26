# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Por hacer
- Pendiente de definir próximas iteraciones

---

## [0.1.0] - 2025-11-26

### Agregado
- Sistema inicial de cálculo de costo de personal
- Modelos de datos: `Empleado` y `CostoPersonal`
- Calculadora de costos con soporte para:
  - Salario base
  - Bonos
  - Horas extra
  - Cargas sociales
  - Beneficios
- Generador de reportes con:
  - Reporte por departamento
  - Reporte de tendencia temporal
  - Métricas clave del proceso
- Exportación a Excel (openpyxl)
- Suite de tests unitarios
- Ejemplo de uso completo

### Sesión de iteración
- **Fecha**: 2025-11-26
- **Objetivo**: Configuración inicial del proyecto y sistema base de reportería
- **Commits relacionados**:
  - `f8059ae` - Initial commit
  - `e22ef34` - Initial plan
  - `eb84d05` - Implement complete personnel cost reporting and metrics system
  - `16d41f3` - Add openpyxl dependency for Excel export functionality

---

## Guía de uso

### Tipos de cambios

- **Agregado** - Nuevas funcionalidades
- **Cambiado** - Cambios en funcionalidades existentes
- **Obsoleto** - Funcionalidades que serán removidas próximamente
- **Eliminado** - Funcionalidades removidas
- **Corregido** - Corrección de bugs
- **Seguridad** - Vulnerabilidades corregidas

### Formato de sesión de iteración

Cada release puede incluir una sección `Sesión de iteración` para documentar:

```markdown
### Sesión de iteración
- **Fecha**: YYYY-MM-DD
- **Objetivo**: Breve descripción del objetivo de la sesión
- **Notas**: Observaciones relevantes (opcional)
- **Commits relacionados**: Lista de commits (opcional)
```

### Versionado

- **MAJOR** (X.0.0): Cambios incompatibles con versiones anteriores
- **MINOR** (0.X.0): Nueva funcionalidad compatible hacia atrás
- **PATCH** (0.0.X): Correcciones de bugs compatibles hacia atrás

---

[Unreleased]: https://github.com/paulrojasj/BC_cosper/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/paulrojasj/BC_cosper/releases/tag/v0.1.0
