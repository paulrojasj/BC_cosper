# COSPER — Diseño de Arquitectura
**Fecha:** 2026-02-19
**Versión:** 1.0 (borrador aprobado)
**URL objetivo:** `belcorp.paulrojasj.com/cosper`
**Repo:** `github.com/paulrojasj/BC_cosper`

---

## 1. Contexto y Objetivo

COSPER (Costo de Personal) es el sistema de control presupuestario de recursos humanos para Belcorp, una empresa con operaciones en +15 países/sociedades. Su objetivo es:

1. **Proyectar** el costo de personal para cada sociedad a lo largo del año
2. **Comparar** versiones de forecast vs plan base y vs año anterior
3. **Descomponer** las variaciones en USD en: efecto tipo de cambio vs variación real del negocio

---

## 2. Posición en la Arquitectura b-connect-plus

```
belcorp.paulrojasj.com
    │
    └── b-connect-plus Gateway Worker
              │
              ├── /estructura/*   → belcorp-estructura-api  (LIVE)
              ├── /cosper/*       → belcorp-cosper-api      (NUEVO)
              ├── /bono/*         → (futuro)
              └── /people-analytics/* → (futuro)
```

COSPER es un **Worker independiente** con su propia D1, conectado al gateway vía Service Binding. Para leer datos de Estructura, COSPER también tiene un Service Binding a `belcorp-estructura-api`.

---

## 3. Cambio Fundamental en el Input de Datos

### Arquitectura anterior (descartada)
> Excel como fuente principal de headcount → COSPER carga todo desde cero

### Arquitectura nueva ✅
> **Estructura como fuente de verdad del headcount** → COSPER importa posiciones aprobadas y enriquece con costos

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE DATOS COSPER                         │
│                                                                  │
│  FUENTE 1: Estructura API                                        │
│  ──────────────────────────────────────────────────────────     │
│  Posiciones donde tiene_cosper = 1                              │
│  (Activos + Vacantes, excluye Eliminar)                         │
│  → nro_plaza, estado, pais, sociedad, ceco, nj, tipo_registro   │
│  → Se sincronizan periódicamente (pull manual o automático)     │
│                                                                  │
│  FUENTE 2: Overrides COSPER                                     │
│  ──────────────────────────────────────────────────────────     │
│  Ajustes sobre el headcount de Estructura:                      │
│  → Cambiar estado de una posición para COSPER                   │
│  → Agregar posiciones nuevas (proyectos especiales)             │
│  → Eliminar posiciones del alcance COSPER                       │
│  → Todos con timestamp, usuario y razón del cambio             │
│                                                                  │
│  FUENTE 3: Enriquecimiento de Costos (Excel upload)             │
│  ──────────────────────────────────────────────────────────     │
│  Solo datos de compensación, no headcount:                      │
│  → Salario base por posición / empleado                        │
│  → Bonos, beneficios, cargas sociales                          │
│  → Proyecciones de incrementos salariales por período          │
│                                                                  │
│  FUENTE 4: Tipos de Cambio                                      │
│  ──────────────────────────────────────────────────────────     │
│  FX presupuestado vs real por sociedad × período               │
│  → Ingreso manual o Excel upload                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Ventaja clave:** cuando el headcount cambia en Estructura (nueva contratación, salida, vacante), COSPER puede sincronizarse y solo necesita actualizar los costos de las posiciones delta.

---

## 4. Modelo de Versiones (Rolling Forecast)

```
Versiones del año fiscal:
  MH    = Must Have / Plan Base (se congela al inicio del año)
  M01   = Real Ene + Proyección Feb-Dic
  M02   = Real Ene-Feb + Proyección Mar-Dic
  ...
  M12   = Real Ene-Nov + Proyección Dic
  Real  = Cierre anual (todos los meses cerrados)
  AA    = Año Anterior (base comparativa histórica)

Estados de versión:
  borrador  → en construcción, editable, puede haber múltiples
  oficial   → cerrada, read-only, es la versión publicada
  historico → versiones de años anteriores
```

**Comparaciones disponibles:**
| Comparación | Significado |
|---|---|
| M02 vs M01 | ¿Cómo cambió mi proyección vs el mes anterior? |
| M02 vs MH | ¿Cuánto me desvío del plan base? |
| M02 vs AA | ¿Cómo voy vs año pasado? |
| Real vs MH | Cierre final vs plan original |

**Vistas de tiempo:**
- **Mensual:** un período específico (YYYY-MM)
- **YTD acumulado:** suma desde enero al mes seleccionado
- **Anual:** suma completa (real + proyección para forecasts)

---

## 5. Motor de Análisis FX — Las Tres Capas

Toda comparación entre dos versiones produce tres capas en USD:

```
FÓRMULAS (por sociedad × período × concepto):

  Presupuesto USD  = Presupuesto LC / FX_presupuesto
  Real/Proy USD    = Real LC / FX_real

  ─────────────────────────────────────────────────────────
  Capa 1: Variación LC (gestión real, sin FX)
    = Real LC - Presupuesto LC
    → "¿Realmente gasté más o menos en moneda local?"

  Capa 2: Efecto FX (impacto del tipo de cambio)
    = (Presupuesto LC / FX_real) - (Presupuesto LC / FX_presupuesto)
    → "¿Cuánto del movimiento en USD es por el TC?"

  Capa 3: Variación total en USD
    = Real USD - Presupuesto USD
    = (Variación LC / FX_real) + Efecto FX
    → "¿Cuánto cambió el gasto en dólares en total?"
  ─────────────────────────────────────────────────────────

  Check: Capa 3 = (Capa 1 / FX_real) + Capa 2  ✓
```

**Lectura ejemplo:**
> Plan: 1,000 USD | Real: 1,150 USD | Variación total: +150 USD
> → Efecto FX: +100 USD (la moneda local se depreció → mismos costos LC valen más en USD)
> → Variación real del negocio: +50 USD (en términos locales también gasté más)

---

## 6. Jerarquía de Navegación

```
Vista Corporativa
    └── por País (agregación de sociedades)
            └── por Sociedad
                    └── por Tipo Registro (Corp / País / Planta)
                            └── por Área / Centro de Costo
                                    └── por Concepto de Costo
```

Cada nivel desglosa las tres capas FX. El usuario puede navegar drill-down.

---

## 7. Modelo de Datos — D1 (SQLite en Cloudflare)

```sql
-- DIMENSIONES
sociedades (id, nombre, pais, moneda_local, tasa_cargas_sociales_default, reglas_json, activa)
versiones (id, nombre, tipo, año, estado, es_version_final, creado_en, cerrado_en)
conceptos_costo (id, nombre, categoria, aplica_a_json)  -- SALARIO_BASE, BONO, etc.

-- HEADCOUNT (sincronizado de Estructura)
cosper_posiciones (
  id, version_id, nro_plaza, silla_estructura,
  estado,           -- Activo | Vacante
  sociedad_id, pais, tipo_registro,  -- Corp | País | Planta
  puesto, nj, ceco_plaza, ceco_nomina,
  fuente,           -- 'estructura' | 'cosper_manual'
  sincronizado_en
)

-- OVERRIDES sobre headcount de Estructura
cosper_overrides (
  id, version_id, nro_plaza,
  campo_modificado, valor_anterior, valor_nuevo,
  razon, usuario, modificado_en
)

-- TIPOS DE CAMBIO (por versión)
tipos_cambio (
  id, version_id, sociedad_id, periodo,  -- YYYY-MM
  tasa_lc_por_usd  -- LC/USD (ej: 3.7 para PEN/USD)
)

-- DATOS DE COSTO (headcount × costo)
data_cosper (
  id, version_id, nro_plaza, sociedad_id,
  periodo,           -- YYYY-MM
  concepto_id,
  importe_lc,        -- monto en moneda local
  importe_usd,       -- pre-calculado = importe_lc / tasa_fx del período
  headcount,         -- FTE (puede ser 0.5 para part-time)
  tipo_dato          -- 'real' | 'proyeccion'
)
```

---

## 8. Estructura del Worker

```
workers/
├── src/
│   ├── index.ts              ← Hono router principal
│   ├── types.ts              ← Env interface (ESTRUCTURA_SERVICE, DB, BASE_PATH)
│   ├── db/
│   │   └── queries.ts        ← D1 helpers (typed)
│   ├── routers/
│   │   ├── sociedades.ts     ← CRUD sociedades + reglas por país
│   │   ├── versiones.ts      ← Gestión de versiones (crear, cerrar, comparar)
│   │   ├── sync.ts           ← POST /sync → pull desde Estructura API
│   │   ├── overrides.ts      ← CRUD overrides con audit trail
│   │   ├── costos.ts         ← Upload Excel de costos + CRUD data_cosper
│   │   ├── fx.ts             ← Tipos de cambio por versión
│   │   └── analisis.ts       ← Queries FX analysis (las 3 capas)
│   └── services/
│       ├── estructura_sync.ts ← Llama a ESTRUCTURA_SERVICE, mapea sillas → cosper_posiciones
│       ├── excel.ts           ← SheetJS: parsea Excel de costos
│       └── fx_calculator.ts   ← Descomposición FX (fórmulas del punto 5)
└── migrations/
    └── 0001_initial.sql
```

---

## 9. Frontend — Páginas Principales (MVP)

```
/cosper/
├── /                   → Dashboard overview (todas las sociedades)
├── /pais/:pais         → Vista agregada por país
├── /sociedad/:id       → Vista detalle una sociedad
│                          → FXAnalysisTable (3 capas)
│                          → Selector versiones (izq vs der)
│                          → Selector tiempo (mes / YTD / anual)
│                          → Drill-down por concepto y ceco
├── /versiones          → Gestión de versiones (crear, ver estado, cerrar)
├── /upload             → Carga de datos: Excel costos, FX, resync Estructura
└── /posiciones/:version → Headcount COSPER: ver posiciones, overrides, diffs
```

---

## 10. Cambios en b-connect-plus

Archivo: `workers/src/types.ts`
```typescript
export interface Env {
  ESTRUCTURA_SERVICE: Fetcher;
  COSPER_SERVICE: Fetcher;     // ← NUEVO
  BASE_PATH: string;
}
```

Archivo: `workers/src/index.ts`
```typescript
// Agregar rutas para cosper
app.all('/cosper/*', forwardToCosper);
app.all('/api/cosper/*', forwardToCosper);
```

Archivo: `workers/wrangler.toml`
```toml
# Agregar en [env.production.services]
{ binding = "COSPER_SERVICE", service = "belcorp-cosper-api" }
```

---

## 11. Scope MVP

| Feature | Estado |
|---|---|
| Sync headcount desde Estructura (tiene_cosper=1) | MVP |
| Ver posiciones COSPER + overrides con audit trail | MVP |
| Upload Excel costos (salario, bonos, beneficios) | MVP |
| Gestión FX rates por versión | MVP |
| Gestión de versiones (MH, M01-M12, Real, AA) | MVP |
| Dashboard análisis FX — 3 capas | MVP |
| Vistas: mensual / YTD / anual | MVP |
| Comparaciones: M-actual vs MH / M-prev / AA | MVP |
| Jerarquía: Corporativo → País → Sociedad | MVP |
| Segmentación: Corp / País / Planta | MVP |
| Control de acceso por sociedad | V2 |
| Flujo aprobación de versiones (draft → oficial workflow) | V2 |
| Alertas y notificaciones | V2 |

---

## 12. Conexión con Arquitectura Data Platform

Según `DATA-PLATFORM-PLAN.md` de b-connect-plus, el COSPER Worker en el futuro emitirá eventos hacia:
- **Cloudflare Pipelines → R2** (Data Lake en formato Iceberg)
- Consultas analíticas cross-proyecto vía **DuckDB-WASM en browser** o **Cloudflare Containers**

Esto permitirá en el futuro correlacionar COSPER con People Analytics, Bono de Resultados y Revisión Salarial.

---

## 13. Estado del Repo

El código Python en `src/costo_personal/` ha sido movido a `legacy/` — la lógica de negocio (calculadora, modelos) será reimplementada en TypeScript dentro del Worker. Los tests y ejemplos existentes sirven como documentación de referencia del dominio.
