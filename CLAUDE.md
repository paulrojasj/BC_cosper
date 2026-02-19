# COSPER — Costo de Personal Belcorp

## Qué es este proyecto

Sistema de control presupuestario de costo de personal para Belcorp (+15 países).
URL de producción: `belcorp.paulrojasj.com/cosper`
Repo: `github.com/paulrojasj/BC_cosper`

## Arquitectura

**Cloudflare Worker** (TypeScript + Hono) + **D1** (SQLite) + **React SPA**.
Conectado al gateway `b-connect-plus` en `belcorp.paulrojasj.com` vía Service Binding.

Ver diseño completo: `docs/plans/2026-02-19-cosper-design.md`

## Repositorios relacionados

| Repo | Descripción | URL |
|---|---|---|
| `b-connect-plus` | Gateway madre — enruta `/cosper/*` a este Worker | `belcorp.paulrojasj.com` |
| `BC_estructura` (Automation) | Fuente de verdad del headcount (Activos + Vacantes) | `belcorp.paulrojasj.com/estructura` |

## Estructura de carpetas

```
workers/          ← Cloudflare Worker (TypeScript + Hono)
  src/
    index.ts      ← Router principal Hono
    types.ts      ← Env interface (ESTRUCTURA_SERVICE, DB, BASE_PATH)
    db/           ← D1 query helpers
    routers/      ← API endpoints por dominio
    services/     ← Lógica de negocio (sync, FX calculator, Excel parser)
  migrations/     ← D1 SQL migrations
  wrangler.toml
  package.json

frontend/         ← React SPA
  src/
    pages/        ← Dashboard, Sociedad, Versiones, Upload, Posiciones
    components/   ← FXAnalysisTable, VersionSelector, SyncStatus, etc.

legacy/           ← Código Python original (v0.1.0) — referencia de dominio
docs/plans/       ← Documentos de diseño y arquitectura
```

## Flujo de datos principal

```
Estructura API (tiene_cosper=1)
    ↓ sync
cosper_posiciones (D1)   ← overrides con audit trail
    +
data_cosper (D1)         ← costos desde Excel upload (salarios, bonos, beneficios)
    +
tipos_cambio (D1)        ← FX presupuesto vs real por período
    ↓
Análisis FX: 3 capas en USD
  1. Variación LC (gestión real)
  2. Efecto FX (impacto tipo de cambio)
  3. Variación total USD
```

## Modelo de versiones

- **MH** = Plan base / Must Have (congelado al inicio del año)
- **M01-M12** = Rolling forecast mensual (real acumulado + proyección)
- **Real** = Cierre anual definitivo
- **AA** = Año anterior (comparativa)

Comparaciones principales: M-actual vs MH | M-actual vs M-anterior | M-actual vs AA

## Fórmulas FX clave

```
Presupuesto USD = Presupuesto LC / FX_presupuesto
Real USD        = Real LC / FX_real

Variación total USD = Real USD - Presupuesto USD
Efecto FX           = (Presupuesto LC / FX_real) - (Presupuesto LC / FX_presupuesto)
Variación real      = Variación total USD - Efecto FX
```

## Comandos de desarrollo

```powershell
# Backend Worker
cd workers
./node_modules/.bin/wrangler dev

# Frontend
cd frontend
npm run dev

# Deploy Worker
cd workers
./node_modules/.bin/wrangler deploy --env production
```

## Puertos (cuando aplique para desarrollo local)
- Frontend: 5175
- Backend (si aplica): 8004

## Notas importantes

- El headcount **NO** se carga por Excel — viene de Estructura API (tiene_cosper=1)
- Los overrides al headcount se auditan: campo, valor anterior, valor nuevo, usuario, razón
- Toda vista en USD; la moneda local es insumo intermedio para calcular el efecto FX
- El Worker necesita Service Binding a `belcorp-estructura-api` para el sync de headcount
- Usar `127.0.0.1` (no localhost) en wrangler.toml para forzar IPv4
