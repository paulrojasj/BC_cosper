# COSPER — Plan de Implementación MVP

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Construir `belcorp.paulrojasj.com/cosper` — sistema de control presupuestario de costo de personal con análisis FX en 3 capas, sincronizado desde Estructura.

**Architecture:** Cloudflare Worker (TypeScript + Hono) con D1 (SQLite) para datos estructurados. React SPA servida desde el Worker. Conectado al gateway b-connect-plus via Service Binding. El headcount base se sincroniza desde la API de Estructura (tiene_cosper=1).

**Tech Stack:** TypeScript, Hono v4, Cloudflare Workers, D1, SheetJS (xlsx), React 18, Vite, Tailwind CSS, Vitest

**Diseño completo:** `docs/plans/2026-02-19-cosper-design.md`

**Worktree local:** `C:\Users\paulrojas\OneDrive - CETCO S.A\Documentos Compartidos\C&A\07. Analytics\Estructura Belcorp\BC_cosper`

---

## Fase 1: Fundación del Worker

### Task 1: Inicializar proyecto Worker (TypeScript + Hono)

**Files:**
- Create: `workers/package.json`
- Create: `workers/tsconfig.json`
- Create: `workers/wrangler.toml`
- Create: `workers/src/index.ts`
- Create: `workers/src/types.ts`

**Step 1: Inicializar npm en workers/**

```bash
cd workers
npm init -y
```

**Step 2: Instalar dependencias**

```bash
npm install hono
npm install --save-dev wrangler @cloudflare/workers-types typescript vitest @cloudflare/vitest-pool-workers
```

**Step 3: Crear `workers/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "types": ["@cloudflare/workers-types"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts"]
}
```

**Step 4: Crear `workers/src/types.ts`**

```typescript
export interface Env {
  DB: D1Database;
  ESTRUCTURA_SERVICE: Fetcher;
  BASE_PATH: string;
}
```

**Step 5: Crear `workers/src/index.ts`**

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import type { Env } from './types';

const PROJECT_ID = 'cosper';
const app = new Hono<{ Bindings: Env }>();

app.use('*', cors({
  origin: ['https://belcorp.paulrojasj.com', 'http://localhost:5175'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}));

app.get(`/api/${PROJECT_ID}/health`, (c) =>
  c.json({ project: PROJECT_ID, status: 'healthy', ts: new Date().toISOString() })
);

app.get(`/api/${PROJECT_ID}/docs`, (c) =>
  c.text('COSPER API — ver /api/cosper/health')
);

export default app;
```

**Step 6: Crear `workers/wrangler.toml`**

```toml
name = "belcorp-cosper-api-staging"
main = "src/index.ts"
compatibility_date = "2025-01-01"
compatibility_flags = ["nodejs_compat"]

routes = []

[vars]
BASE_PATH = ""

[[d1_databases]]
binding = "DB"
database_name = "cosper-db-staging"
database_id = "PLACEHOLDER_STAGING"

[[services]]
binding = "ESTRUCTURA_SERVICE"
service = "belcorp-estructura-api-staging"

# ─── PRODUCCIÓN ───────────────────────────────────────────────
[env.production]
name = "belcorp-cosper-api"
routes = []

[env.production.vars]
BASE_PATH = ""

[[env.production.d1_databases]]
binding = "DB"
database_name = "cosper-db"
database_id = "PLACEHOLDER_PROD"

[[env.production.services]]
binding = "ESTRUCTURA_SERVICE"
service = "belcorp-estructura-api"
```

**Step 7: Crear `workers/package.json` scripts**

```json
{
  "name": "cosper-worker",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "./node_modules/.bin/wrangler dev",
    "deploy:staging": "./node_modules/.bin/wrangler deploy",
    "deploy:prod": "./node_modules/.bin/wrangler deploy --env production",
    "test": "./node_modules/.bin/vitest run",
    "test:watch": "./node_modules/.bin/vitest"
  }
}
```

**Step 8: Verificar que compila**

```bash
cd workers
./node_modules/.bin/wrangler dev --local
```

Esperado: servidor en `http://localhost:8787`, `GET /api/cosper/health` responde `{"project":"cosper","status":"healthy"}`

**Step 9: Commit**

```bash
git add workers/
git commit -m "feat(worker): inicializar Worker con Hono y health endpoint"
```

---

### Task 2: Crear base de datos D1 y migraciones

**Files:**
- Create: `workers/migrations/0001_initial.sql`
- Create: `workers/migrations/0002_seed.sql`

**Step 1: Crear `workers/migrations/0001_initial.sql`**

```sql
-- Sociedades (entidades por país)
CREATE TABLE IF NOT EXISTS sociedades (
  id          TEXT PRIMARY KEY,           -- 'PE01', 'CO01', 'BR01'
  nombre      TEXT NOT NULL,
  pais        TEXT NOT NULL,              -- 'PE', 'CO', 'BR', 'MX', 'EC', 'BO', 'CL'
  moneda_local TEXT NOT NULL,             -- 'PEN', 'COP', 'BRL', 'MXN', 'USD', 'BOB', 'CLP'
  tasa_cargas_default REAL DEFAULT 0.25,
  reglas_json TEXT NOT NULL DEFAULT '{}',
  activa      INTEGER NOT NULL DEFAULT 1,
  creado_en   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Versiones del año fiscal
CREATE TABLE IF NOT EXISTS versiones (
  id          TEXT PRIMARY KEY,           -- 'MH_2026', 'M01_2026', 'Real_2026', 'AA_2025'
  nombre      TEXT NOT NULL,
  tipo        TEXT NOT NULL,              -- 'plan' | 'forecast' | 'real' | 'historico'
  anio        INTEGER NOT NULL,
  estado      TEXT NOT NULL DEFAULT 'borrador',  -- 'borrador' | 'oficial' | 'historico'
  creado_en   TEXT NOT NULL DEFAULT (datetime('now')),
  cerrado_en  TEXT
);

-- Catálogo de conceptos de costo
CREATE TABLE IF NOT EXISTS conceptos_costo (
  id          TEXT PRIMARY KEY,           -- 'SALARIO_BASE', 'BONO', etc.
  nombre      TEXT NOT NULL,
  categoria   TEXT NOT NULL,              -- 'SALARIO' | 'VARIABLE' | 'BENEFICIOS' | 'CARGAS_SOCIALES' | 'OTROS'
  activo      INTEGER NOT NULL DEFAULT 1
);

-- Posiciones COSPER (sync desde Estructura)
CREATE TABLE IF NOT EXISTS cosper_posiciones (
  id              TEXT NOT NULL,          -- version_id + '|' + nro_plaza
  version_id      TEXT NOT NULL,
  nro_plaza       TEXT NOT NULL,
  silla_estructura TEXT,
  estado          TEXT NOT NULL,          -- 'Activo' | 'Vacante'
  sociedad_id     TEXT NOT NULL,
  pais            TEXT,
  tipo_registro   TEXT,                   -- 'Corp' | 'País' | 'Planta'
  puesto          TEXT,
  nj              TEXT,
  ceco_plaza      TEXT,
  ceco_nomina     TEXT,
  nombre_ocupante TEXT,
  fuente          TEXT NOT NULL DEFAULT 'estructura',
  sincronizado_en TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (version_id, nro_plaza),
  FOREIGN KEY (version_id)  REFERENCES versiones(id),
  FOREIGN KEY (sociedad_id) REFERENCES sociedades(id)
);

-- Overrides con audit trail
CREATE TABLE IF NOT EXISTS cosper_overrides (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  version_id      TEXT NOT NULL,
  nro_plaza       TEXT NOT NULL,
  campo_modificado TEXT NOT NULL,
  valor_anterior  TEXT,
  valor_nuevo     TEXT,
  razon           TEXT,
  usuario         TEXT NOT NULL DEFAULT 'system',
  modificado_en   TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (version_id) REFERENCES versiones(id)
);

-- Tipos de cambio (por versión × sociedad × período)
CREATE TABLE IF NOT EXISTS tipos_cambio (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  version_id  TEXT NOT NULL,
  sociedad_id TEXT NOT NULL,
  periodo     TEXT NOT NULL,              -- 'YYYY-MM'
  tasa_lc_por_usd REAL NOT NULL,         -- LC/USD (ej: 3.7 → 1 USD = 3.7 PEN)
  FOREIGN KEY (version_id)  REFERENCES versiones(id),
  FOREIGN KEY (sociedad_id) REFERENCES sociedades(id),
  UNIQUE(version_id, sociedad_id, periodo)
);

-- Data de costo (posición × período × concepto)
CREATE TABLE IF NOT EXISTS data_cosper (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  version_id  TEXT NOT NULL,
  nro_plaza   TEXT NOT NULL,
  sociedad_id TEXT NOT NULL,
  periodo     TEXT NOT NULL,              -- 'YYYY-MM'
  concepto_id TEXT NOT NULL,
  importe_lc  REAL NOT NULL DEFAULT 0,   -- monto en moneda local
  importe_usd REAL,                       -- pre-calculado
  headcount   REAL NOT NULL DEFAULT 1.0, -- FTE
  tipo_dato   TEXT NOT NULL,             -- 'real' | 'proyeccion'
  FOREIGN KEY (version_id)  REFERENCES versiones(id),
  FOREIGN KEY (sociedad_id) REFERENCES sociedades(id),
  FOREIGN KEY (concepto_id) REFERENCES conceptos_costo(id)
);

-- Índices de performance
CREATE INDEX IF NOT EXISTS idx_data_version    ON data_cosper(version_id);
CREATE INDEX IF NOT EXISTS idx_data_sociedad   ON data_cosper(sociedad_id, periodo);
CREATE INDEX IF NOT EXISTS idx_pos_version     ON cosper_posiciones(version_id);
CREATE INDEX IF NOT EXISTS idx_tc_version      ON tipos_cambio(version_id, sociedad_id);
```

**Step 2: Crear `workers/migrations/0002_seed.sql`** (datos iniciales de catálogo)

```sql
-- Conceptos de costo estándar
INSERT OR IGNORE INTO conceptos_costo (id, nombre, categoria) VALUES
  ('SALARIO_BASE',        'Salario Base',              'SALARIO'),
  ('GRATIFICACION',       'Gratificación / Aguinaldo',  'SALARIO'),
  ('BONO_DESEMPENO',      'Bono de Desempeño',          'VARIABLE'),
  ('BONO_VENTAS',         'Bono de Ventas',             'VARIABLE'),
  ('BENEFICIOS_SALUD',    'Beneficios de Salud',        'BENEFICIOS'),
  ('BENEFICIOS_OTROS',    'Otros Beneficios',           'BENEFICIOS'),
  ('CARGAS_SOCIALES',     'Cargas Sociales / ESSALUD',  'CARGAS_SOCIALES'),
  ('CTS',                 'CTS / Compensación',         'CARGAS_SOCIALES'),
  ('VACACIONES',          'Vacaciones',                 'CARGAS_SOCIALES'),
  ('OTROS',               'Otros Costos',               'OTROS');
```

**Step 3: Crear D1 en Cloudflare (staging)**

```powershell
# En PowerShell (no Git Bash)
cd workers
./node_modules/.bin/wrangler d1 create cosper-db-staging
```

Copiar el `database_id` que devuelve y actualizar `wrangler.toml` en `PLACEHOLDER_STAGING`.

**Step 4: Aplicar migraciones**

```powershell
./node_modules/.bin/wrangler d1 execute cosper-db-staging --file=migrations/0001_initial.sql
./node_modules/.bin/wrangler d1 execute cosper-db-staging --file=migrations/0002_seed.sql
```

Esperado: `✅ Successfully executed SQL`

**Step 5: Verificar tablas creadas**

```powershell
./node_modules/.bin/wrangler d1 execute cosper-db-staging --command="SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
```

Esperado: 7 tablas listadas.

**Step 6: Commit**

```bash
git add workers/migrations/
git commit -m "feat(db): agregar schema D1 y seed de conceptos de costo"
```

---

## Fase 2: Servicios Core

### Task 3: Motor FX — TDD del calculador de varianzas

**Files:**
- Create: `workers/src/services/fx_calculator.ts`
- Create: `workers/src/services/fx_calculator.test.ts`

**Step 1: Crear `workers/src/services/fx_calculator.test.ts`**

```typescript
import { describe, it, expect } from 'vitest';
import { calcularAnalisisFX, calcularAnalisisFXAgregado } from './fx_calculator';

describe('calcularAnalisisFX', () => {
  it('calcula variación cero cuando presupuesto = real', () => {
    const result = calcularAnalisisFX({
      presupuesto_lc: 1000,
      real_lc: 1000,
      fx_presupuesto: 3.7,
      fx_real: 3.7,
    });
    expect(result.variacion_total_usd).toBeCloseTo(0);
    expect(result.efecto_fx).toBeCloseTo(0);
    expect(result.variacion_lc).toBeCloseTo(0);
  });

  it('aísla efecto FX cuando el LC no cambia pero el TC sí', () => {
    // Presupuesto: 1000 LC / 3.7 = 270.27 USD
    // Real: 1000 LC / 4.0 = 250.00 USD  (moneda local se depreció)
    const result = calcularAnalisisFX({
      presupuesto_lc: 1000,
      real_lc: 1000,
      fx_presupuesto: 3.7,
      fx_real: 4.0,
    });
    expect(result.variacion_lc).toBeCloseTo(0);          // No cambió el gasto local
    expect(result.efecto_fx).toBeCloseTo(-20.27, 1);     // TC impactó negativamente en USD
    expect(result.variacion_real_negocio_usd).toBeCloseTo(0, 1); // Negocio no cambió
    expect(result.variacion_total_usd).toBeCloseTo(-20.27, 1);
  });

  it('aísla variación real cuando el TC no cambia pero el LC sí', () => {
    // Gasté 1100 LC en vez de 1000 LC, TC igual
    const result = calcularAnalisisFX({
      presupuesto_lc: 1000,
      real_lc: 1100,
      fx_presupuesto: 3.7,
      fx_real: 3.7,
    });
    expect(result.variacion_lc).toBeCloseTo(100);        // Gasté 100 LC más
    expect(result.efecto_fx).toBeCloseTo(0);             // TC no cambió
    expect(result.variacion_real_negocio_usd).toBeCloseTo(100 / 3.7, 1);
  });

  it('descompone correctamente con ambos efectos simultáneos', () => {
    const result = calcularAnalisisFX({
      presupuesto_lc: 1000,
      real_lc: 1100,
      fx_presupuesto: 3.7,
      fx_real: 4.0,
    });
    // Check: variación_total = (variación_lc / fx_real) + efecto_fx
    const check = (result.variacion_lc / 4.0) + result.efecto_fx;
    expect(result.variacion_total_usd).toBeCloseTo(check, 6);
  });

  it('maneja fx_real = 0 sin dividir por cero', () => {
    const result = calcularAnalisisFX({
      presupuesto_lc: 1000,
      real_lc: 1000,
      fx_presupuesto: 3.7,
      fx_real: 0,
    });
    expect(result.real_usd).toBe(0);
    expect(Number.isNaN(result.variacion_total_usd)).toBe(false);
  });
});

describe('calcularAnalisisFXAgregado', () => {
  it('suma correctamente múltiples períodos', () => {
    const periodos = [
      { presupuesto_lc: 1000, real_lc: 1100, fx_presupuesto: 3.7, fx_real: 3.8 },
      { presupuesto_lc: 1000, real_lc: 900,  fx_presupuesto: 3.7, fx_real: 3.9 },
    ];
    const result = calcularAnalisisFXAgregado(periodos);
    expect(result.variacion_lc).toBeCloseTo(0);  // +100 - 100
    expect(result.variacion_total_usd).toBeCloseTo(
      periodos.reduce((sum, p) => {
        const usd = calcularAnalisisFX(p);
        return sum + usd.variacion_total_usd;
      }, 0), 6
    );
  });
});
```

**Step 2: Ejecutar test para confirmar que falla**

```bash
cd workers
./node_modules/.bin/vitest run src/services/fx_calculator.test.ts
```

Esperado: FAIL — `Cannot find module './fx_calculator'`

**Step 3: Crear `workers/src/services/fx_calculator.ts`**

```typescript
export interface FXPeriodData {
  presupuesto_lc: number;
  real_lc: number;
  fx_presupuesto: number;   // LC/USD — ej: 3.7 significa 1 USD = 3.7 LC
  fx_real: number;
}

export interface FXAnalysis {
  presupuesto_usd: number;
  real_usd: number;
  variacion_lc: number;                 // Capa 1: Real LC - Ppto LC
  efecto_fx: number;                    // Capa 2: impacto del TC en USD
  variacion_total_usd: number;          // Capa 3: Real USD - Ppto USD
  variacion_real_negocio_usd: number;   // Capa 3 - Capa 2
}

export function calcularAnalisisFX(data: FXPeriodData): FXAnalysis {
  const presupuesto_usd = data.fx_presupuesto !== 0
    ? data.presupuesto_lc / data.fx_presupuesto
    : 0;

  const real_usd = data.fx_real !== 0
    ? data.real_lc / data.fx_real
    : 0;

  const variacion_lc = data.real_lc - data.presupuesto_lc;

  // Efecto FX: cuánto se movió el USD solo por el cambio en TC
  // = Ppto_LC/FX_real  vs  Ppto_LC/FX_ppto  (holding LC constant)
  const efecto_fx = (data.fx_real !== 0 && data.fx_presupuesto !== 0)
    ? (data.presupuesto_lc / data.fx_real) - (data.presupuesto_lc / data.fx_presupuesto)
    : 0;

  const variacion_total_usd = real_usd - presupuesto_usd;
  const variacion_real_negocio_usd = variacion_total_usd - efecto_fx;

  return {
    presupuesto_usd,
    real_usd,
    variacion_lc,
    efecto_fx,
    variacion_total_usd,
    variacion_real_negocio_usd,
  };
}

export function calcularAnalisisFXAgregado(periodos: FXPeriodData[]): FXAnalysis {
  return periodos.reduce<FXAnalysis>(
    (acc, p) => {
      const r = calcularAnalisisFX(p);
      return {
        presupuesto_usd:            acc.presupuesto_usd            + r.presupuesto_usd,
        real_usd:                   acc.real_usd                   + r.real_usd,
        variacion_lc:               acc.variacion_lc               + r.variacion_lc,
        efecto_fx:                  acc.efecto_fx                  + r.efecto_fx,
        variacion_total_usd:        acc.variacion_total_usd        + r.variacion_total_usd,
        variacion_real_negocio_usd: acc.variacion_real_negocio_usd + r.variacion_real_negocio_usd,
      };
    },
    { presupuesto_usd: 0, real_usd: 0, variacion_lc: 0,
      efecto_fx: 0, variacion_total_usd: 0, variacion_real_negocio_usd: 0 }
  );
}
```

**Step 4: Ejecutar tests**

```bash
./node_modules/.bin/vitest run src/services/fx_calculator.test.ts
```

Esperado: 6 tests PASS

**Step 5: Commit**

```bash
git add workers/src/services/
git commit -m "feat(fx): implementar motor de análisis FX con TDD (3 capas)"
```

---

### Task 4: D1 Query Helpers (capa de acceso a datos)

**Files:**
- Create: `workers/src/db/queries.ts`

**Step 1: Crear `workers/src/db/queries.ts`**

```typescript
import type { D1Database } from '@cloudflare/workers-types';

// ── TIPOS ────────────────────────────────────────────────────────────────────

export interface Sociedad {
  id: string; nombre: string; pais: string; moneda_local: string;
  tasa_cargas_default: number; reglas_json: string; activa: number;
}

export interface Version {
  id: string; nombre: string; tipo: string; anio: number;
  estado: string; creado_en: string; cerrado_en: string | null;
}

export interface CosperPosicion {
  version_id: string; nro_plaza: string; silla_estructura: string | null;
  estado: string; sociedad_id: string; pais: string | null;
  tipo_registro: string | null; puesto: string | null; nj: string | null;
  ceco_plaza: string | null; ceco_nomina: string | null;
  nombre_ocupante: string | null; fuente: string;
}

export interface TipoCambio {
  version_id: string; sociedad_id: string; periodo: string; tasa_lc_por_usd: number;
}

export interface DataCosper {
  version_id: string; nro_plaza: string; sociedad_id: string;
  periodo: string; concepto_id: string; importe_lc: number;
  importe_usd: number | null; headcount: number; tipo_dato: string;
}

// ── SOCIEDADES ────────────────────────────────────────────────────────────────

export const db = {
  sociedades: {
    async list(d1: D1Database): Promise<Sociedad[]> {
      return d1.prepare('SELECT * FROM sociedades WHERE activa = 1 ORDER BY pais, id')
        .all<Sociedad>().then(r => r.results);
    },
    async get(d1: D1Database, id: string): Promise<Sociedad | null> {
      return d1.prepare('SELECT * FROM sociedades WHERE id = ?').bind(id).first<Sociedad>();
    },
    async upsert(d1: D1Database, s: Omit<Sociedad, 'creado_en'>): Promise<void> {
      await d1.prepare(`
        INSERT INTO sociedades (id, nombre, pais, moneda_local, tasa_cargas_default, reglas_json, activa)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          nombre = excluded.nombre, pais = excluded.pais,
          moneda_local = excluded.moneda_local,
          tasa_cargas_default = excluded.tasa_cargas_default,
          reglas_json = excluded.reglas_json, activa = excluded.activa
      `).bind(s.id, s.nombre, s.pais, s.moneda_local, s.tasa_cargas_default, s.reglas_json, s.activa).run();
    },
  },

  versiones: {
    async list(d1: D1Database, anio?: number): Promise<Version[]> {
      const q = anio
        ? d1.prepare('SELECT * FROM versiones WHERE anio = ? ORDER BY id').bind(anio)
        : d1.prepare('SELECT * FROM versiones ORDER BY anio DESC, id');
      return q.all<Version>().then(r => r.results);
    },
    async get(d1: D1Database, id: string): Promise<Version | null> {
      return d1.prepare('SELECT * FROM versiones WHERE id = ?').bind(id).first<Version>();
    },
    async create(d1: D1Database, v: Omit<Version, 'creado_en' | 'cerrado_en'>): Promise<void> {
      await d1.prepare(`
        INSERT INTO versiones (id, nombre, tipo, anio, estado)
        VALUES (?, ?, ?, ?, ?)
      `).bind(v.id, v.nombre, v.tipo, v.anio, v.estado).run();
    },
    async cerrar(d1: D1Database, id: string): Promise<void> {
      await d1.prepare(`
        UPDATE versiones SET estado = 'oficial', cerrado_en = datetime('now') WHERE id = ?
      `).bind(id).run();
    },
  },

  posiciones: {
    async listByVersion(d1: D1Database, versionId: string, sociedadId?: string): Promise<CosperPosicion[]> {
      const q = sociedadId
        ? d1.prepare('SELECT * FROM cosper_posiciones WHERE version_id = ? AND sociedad_id = ?').bind(versionId, sociedadId)
        : d1.prepare('SELECT * FROM cosper_posiciones WHERE version_id = ?').bind(versionId);
      return q.all<CosperPosicion>().then(r => r.results);
    },
    async upsertBatch(d1: D1Database, posiciones: CosperPosicion[]): Promise<void> {
      const stmt = d1.prepare(`
        INSERT INTO cosper_posiciones
          (version_id, nro_plaza, silla_estructura, estado, sociedad_id, pais,
           tipo_registro, puesto, nj, ceco_plaza, ceco_nomina, nombre_ocupante, fuente)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(version_id, nro_plaza) DO UPDATE SET
          estado = excluded.estado, silla_estructura = excluded.silla_estructura,
          puesto = excluded.puesto, nj = excluded.nj,
          ceco_plaza = excluded.ceco_plaza, nombre_ocupante = excluded.nombre_ocupante,
          sincronizado_en = datetime('now')
      `);
      await d1.batch(posiciones.map(p =>
        stmt.bind(p.version_id, p.nro_plaza, p.silla_estructura, p.estado,
          p.sociedad_id, p.pais, p.tipo_registro, p.puesto, p.nj,
          p.ceco_plaza, p.ceco_nomina, p.nombre_ocupante, p.fuente)
      ));
    },
  },

  tiposCambio: {
    async listByVersion(d1: D1Database, versionId: string, sociedadId?: string): Promise<TipoCambio[]> {
      const q = sociedadId
        ? d1.prepare('SELECT * FROM tipos_cambio WHERE version_id = ? AND sociedad_id = ? ORDER BY periodo').bind(versionId, sociedadId)
        : d1.prepare('SELECT * FROM tipos_cambio WHERE version_id = ? ORDER BY sociedad_id, periodo').bind(versionId);
      return q.all<TipoCambio>().then(r => r.results);
    },
    async upsert(d1: D1Database, tc: TipoCambio): Promise<void> {
      await d1.prepare(`
        INSERT INTO tipos_cambio (version_id, sociedad_id, periodo, tasa_lc_por_usd)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(version_id, sociedad_id, periodo) DO UPDATE SET tasa_lc_por_usd = excluded.tasa_lc_por_usd
      `).bind(tc.version_id, tc.sociedad_id, tc.periodo, tc.tasa_lc_por_usd).run();
    },
  },

  dataCosper: {
    async getAnalisis(
      d1: D1Database,
      versionBaseId: string,
      versionCompId: string,
      filtros: { sociedad_id?: string; periodo?: string; periodo_hasta?: string }
    ) {
      // Consulta principal: comparar dos versiones con sus FX
      const whereBase = filtros.sociedad_id ? 'AND d.sociedad_id = ?' : '';
      const periodoFilter = filtros.periodo
        ? (filtros.periodo_hasta
          ? "AND d.periodo BETWEEN ? AND ?"
          : "AND d.periodo = ?")
        : '';

      const sql = `
        SELECT
          d.sociedad_id,
          d.periodo,
          d.concepto_id,
          s.moneda_local,
          s.pais,
          SUM(CASE WHEN d.version_id = ? THEN d.importe_lc ELSE 0 END) as ppto_lc,
          SUM(CASE WHEN d.version_id = ? THEN d.importe_lc ELSE 0 END) as real_lc,
          MAX(CASE WHEN d.version_id = ? THEN tc_b.tasa_lc_por_usd ELSE NULL END) as fx_ppto,
          MAX(CASE WHEN d.version_id = ? THEN tc_c.tasa_lc_por_usd ELSE NULL END) as fx_real
        FROM data_cosper d
        JOIN sociedades s ON d.sociedad_id = s.id
        LEFT JOIN tipos_cambio tc_b ON tc_b.version_id = ? AND tc_b.sociedad_id = d.sociedad_id AND tc_b.periodo = d.periodo
        LEFT JOIN tipos_cambio tc_c ON tc_c.version_id = ? AND tc_c.sociedad_id = d.sociedad_id AND tc_c.periodo = d.periodo
        WHERE d.version_id IN (?, ?) ${whereBase} ${periodoFilter}
        GROUP BY d.sociedad_id, d.periodo, d.concepto_id, s.moneda_local, s.pais
        ORDER BY s.pais, d.sociedad_id, d.periodo, d.concepto_id
      `;

      const params: unknown[] = [
        versionBaseId, versionCompId,
        versionBaseId, versionCompId,
        versionBaseId, versionCompId,
        versionBaseId, versionCompId,
      ];
      if (filtros.sociedad_id) params.push(filtros.sociedad_id);
      if (filtros.periodo) params.push(filtros.periodo);
      if (filtros.periodo_hasta) params.push(filtros.periodo_hasta);

      return d1.prepare(sql).bind(...params).all();
    },
  },
};
```

**Step 2: Commit**

```bash
git add workers/src/db/
git commit -m "feat(db): agregar query helpers tipados para D1"
```

---

## Fase 3: API Endpoints

### Task 5: Routers — Sociedades y Versiones

**Files:**
- Create: `workers/src/routers/sociedades.ts`
- Create: `workers/src/routers/versiones.ts`
- Modify: `workers/src/index.ts`

**Step 1: Crear `workers/src/routers/sociedades.ts`**

```typescript
import { Hono } from 'hono';
import { db } from '../db/queries';
import type { Env } from '../types';

export const sociedadesRouter = new Hono<{ Bindings: Env }>();

// GET /api/cosper/v1/sociedades
sociedadesRouter.get('/', async (c) => {
  const list = await db.sociedades.list(c.env.DB);
  return c.json({ data: list });
});

// GET /api/cosper/v1/sociedades/:id
sociedadesRouter.get('/:id', async (c) => {
  const s = await db.sociedades.get(c.env.DB, c.req.param('id'));
  if (!s) return c.json({ error: 'Sociedad no encontrada' }, 404);
  return c.json({ data: s });
});

// POST /api/cosper/v1/sociedades
sociedadesRouter.post('/', async (c) => {
  const body = await c.req.json();
  if (!body.id || !body.nombre || !body.pais || !body.moneda_local) {
    return c.json({ error: 'Campos requeridos: id, nombre, pais, moneda_local' }, 400);
  }
  await db.sociedades.upsert(c.env.DB, {
    id: body.id, nombre: body.nombre, pais: body.pais,
    moneda_local: body.moneda_local,
    tasa_cargas_default: body.tasa_cargas_default ?? 0.25,
    reglas_json: JSON.stringify(body.reglas ?? {}),
    activa: 1,
  });
  return c.json({ ok: true }, 201);
});
```

**Step 2: Crear `workers/src/routers/versiones.ts`**

```typescript
import { Hono } from 'hono';
import { db } from '../db/queries';
import type { Env } from '../types';

export const versionesRouter = new Hono<{ Bindings: Env }>();

// GET /api/cosper/v1/versiones?anio=2026
versionesRouter.get('/', async (c) => {
  const anio = c.req.query('anio') ? parseInt(c.req.query('anio')!) : undefined;
  const list = await db.versiones.list(c.env.DB, anio);
  return c.json({ data: list });
});

// GET /api/cosper/v1/versiones/:id
versionesRouter.get('/:id', async (c) => {
  const v = await db.versiones.get(c.env.DB, c.req.param('id'));
  if (!v) return c.json({ error: 'Versión no encontrada' }, 404);
  return c.json({ data: v });
});

// POST /api/cosper/v1/versiones
versionesRouter.post('/', async (c) => {
  const body = await c.req.json();
  const tipos = ['plan', 'forecast', 'real', 'historico'];
  if (!body.id || !body.nombre || !tipos.includes(body.tipo) || !body.anio) {
    return c.json({ error: 'Campos requeridos: id, nombre, tipo (plan|forecast|real|historico), anio' }, 400);
  }
  await db.versiones.create(c.env.DB, {
    id: body.id, nombre: body.nombre, tipo: body.tipo,
    anio: body.anio, estado: 'borrador',
  });
  return c.json({ ok: true, id: body.id }, 201);
});

// POST /api/cosper/v1/versiones/:id/cerrar
versionesRouter.post('/:id/cerrar', async (c) => {
  const v = await db.versiones.get(c.env.DB, c.req.param('id'));
  if (!v) return c.json({ error: 'Versión no encontrada' }, 404);
  if (v.estado === 'oficial') return c.json({ error: 'Versión ya está cerrada' }, 400);
  await db.versiones.cerrar(c.env.DB, c.req.param('id'));
  return c.json({ ok: true });
});
```

**Step 3: Actualizar `workers/src/index.ts` para incluir routers**

Reemplazar el contenido con:

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { sociedadesRouter } from './routers/sociedades';
import { versionesRouter } from './routers/versiones';
import type { Env } from './types';

const PROJECT_ID = 'cosper';
const BASE = `/api/${PROJECT_ID}/v1`;

const app = new Hono<{ Bindings: Env }>();

app.use('*', cors({
  origin: ['https://belcorp.paulrojasj.com', 'http://localhost:5175'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}));

app.get(`/api/${PROJECT_ID}/health`, (c) =>
  c.json({ project: PROJECT_ID, status: 'healthy', ts: new Date().toISOString() })
);

app.route(`${BASE}/sociedades`, sociedadesRouter);
app.route(`${BASE}/versiones`, versionesRouter);

export default app;
```

**Step 4: Probar localmente**

```bash
cd workers
./node_modules/.bin/wrangler dev --local --persist-to .wrangler/state
```

Luego en otra terminal:

```bash
# Crear una sociedad
curl -X POST http://localhost:8787/api/cosper/v1/sociedades \
  -H "Content-Type: application/json" \
  -d '{"id":"PE01","nombre":"Belcorp Peru","pais":"PE","moneda_local":"PEN"}'

# Listar sociedades
curl http://localhost:8787/api/cosper/v1/sociedades

# Crear versión MH 2026
curl -X POST http://localhost:8787/api/cosper/v1/versiones \
  -H "Content-Type: application/json" \
  -d '{"id":"MH_2026","nombre":"Must Have 2026","tipo":"plan","anio":2026}'
```

**Step 5: Commit**

```bash
git add workers/src/
git commit -m "feat(api): agregar routers de sociedades y versiones"
```

---

### Task 6: Sync desde Estructura + Overrides

**Files:**
- Create: `workers/src/services/estructura_sync.ts`
- Create: `workers/src/routers/sync.ts`
- Create: `workers/src/routers/overrides.ts`
- Modify: `workers/src/index.ts`

**Step 1: Crear `workers/src/services/estructura_sync.ts`**

```typescript
import type { Fetcher } from '@cloudflare/workers-types';
import type { CosperPosicion } from '../db/queries';

interface SillaEstructura {
  nro_plaza: string;
  silla: string;
  estado_visual: string;   // 'Ocupada' | 'Vacante'
  tiene_cosper: number;
  sociedad_id?: string;    // se mapea desde cia/prefijo_agrupado
  pais_unico: string;
  tipo_registro: string;   // 'Corp' | 'Pais' | 'Planta'
  puesto: string;
  nj: string;
  ceco_plaza: string;
  ceco_nomina: string;
  nombre?: string;         // PII
  cia: string;
  prefijo_agrupado: string;
}

// Mapeo de cia/prefijo a sociedad_id COSPER
// (completar con las sociedades reales de Belcorp)
const CIA_TO_SOCIEDAD: Record<string, string> = {
  'PE01': 'PE01', 'CO01': 'CO01', 'BR01': 'BR01', 'MX01': 'MX01',
  'EC01': 'EC01', 'BO01': 'BO01', 'CL01': 'CL01',
  // Agregar el mapeo real según las cías de Belcorp
};

export async function syncDesdeEstructura(
  estructuraService: Fetcher,
  versionId: string,
  fecha: string,  // YYYY-MM-DD — snapshot date
  pageSize = 5000
): Promise<{ posiciones: CosperPosicion[]; total: number; errores: string[] }> {
  const errores: string[] = [];
  const posiciones: CosperPosicion[] = [];
  let page = 1;
  let totalPaginas = 1;

  while (page <= totalPaginas) {
    const url = `/api/estructura/v1/estructura/?fecha=${fecha}&tiene_cosper=1&page=${page}&page_size=${pageSize}`;
    const resp = await estructuraService.fetch(new Request(`http://internal${url}`));

    if (!resp.ok) {
      errores.push(`Error al consultar Estructura página ${page}: ${resp.status}`);
      break;
    }

    const data = await resp.json<{ items: SillaEstructura[]; total: number; pages: number }>();
    totalPaginas = data.pages;

    for (const silla of data.items) {
      const sociedad_id = CIA_TO_SOCIEDAD[silla.cia] ?? silla.cia;
      const estado = silla.estado_visual === 'Ocupada' ? 'Activo' : 'Vacante';

      posiciones.push({
        version_id: versionId,
        nro_plaza: silla.nro_plaza,
        silla_estructura: silla.silla,
        estado,
        sociedad_id,
        pais: silla.pais_unico,
        tipo_registro: silla.tipo_registro,
        puesto: silla.puesto,
        nj: silla.nj,
        ceco_plaza: silla.ceco_plaza,
        ceco_nomina: silla.ceco_nomina,
        nombre_ocupante: silla.nombre ?? null,
        fuente: 'estructura',
      });
    }

    page++;
  }

  return { posiciones, total: posiciones.length, errores };
}
```

**Step 2: Crear `workers/src/routers/sync.ts`**

```typescript
import { Hono } from 'hono';
import { db } from '../db/queries';
import { syncDesdeEstructura } from '../services/estructura_sync';
import type { Env } from '../types';

export const syncRouter = new Hono<{ Bindings: Env }>();

// POST /api/cosper/v1/sync
// Body: { version_id, fecha }
syncRouter.post('/', async (c) => {
  const body = await c.req.json<{ version_id: string; fecha: string }>();

  if (!body.version_id || !body.fecha) {
    return c.json({ error: 'Se requiere version_id y fecha (YYYY-MM-DD)' }, 400);
  }

  const version = await db.versiones.get(c.env.DB, body.version_id);
  if (!version) return c.json({ error: 'Versión no encontrada' }, 404);
  if (version.estado === 'oficial') return c.json({ error: 'No se puede sincronizar una versión oficial' }, 400);

  const { posiciones, total, errores } = await syncDesdeEstructura(
    c.env.ESTRUCTURA_SERVICE,
    body.version_id,
    body.fecha
  );

  if (posiciones.length > 0) {
    await db.posiciones.upsertBatch(c.env.DB, posiciones);
  }

  return c.json({
    ok: true,
    sincronizados: total,
    errores: errores.length > 0 ? errores : undefined,
  });
});

// GET /api/cosper/v1/sync/posiciones?version_id=MH_2026&sociedad_id=PE01
syncRouter.get('/posiciones', async (c) => {
  const version_id = c.req.query('version_id');
  const sociedad_id = c.req.query('sociedad_id');
  if (!version_id) return c.json({ error: 'Se requiere version_id' }, 400);
  const posiciones = await db.posiciones.listByVersion(c.env.DB, version_id, sociedad_id);
  return c.json({ data: posiciones, total: posiciones.length });
});
```

**Step 3: Crear `workers/src/routers/overrides.ts`**

```typescript
import { Hono } from 'hono';
import type { Env } from '../types';

export const overridesRouter = new Hono<{ Bindings: Env }>();

// GET /api/cosper/v1/overrides?version_id=MH_2026&nro_plaza=123456
overridesRouter.get('/', async (c) => {
  const { version_id, nro_plaza } = c.req.query();
  if (!version_id) return c.json({ error: 'Se requiere version_id' }, 400);

  const q = nro_plaza
    ? c.env.DB.prepare('SELECT * FROM cosper_overrides WHERE version_id = ? AND nro_plaza = ? ORDER BY modificado_en DESC').bind(version_id, nro_plaza)
    : c.env.DB.prepare('SELECT * FROM cosper_overrides WHERE version_id = ? ORDER BY modificado_en DESC').bind(version_id);

  const result = await q.all();
  return c.json({ data: result.results });
});

// POST /api/cosper/v1/overrides
// Registra un cambio y actualiza la posición
overridesRouter.post('/', async (c) => {
  const body = await c.req.json<{
    version_id: string; nro_plaza: string;
    campo_modificado: string; valor_nuevo: string;
    razon?: string; usuario?: string;
  }>();

  if (!body.version_id || !body.nro_plaza || !body.campo_modificado || body.valor_nuevo === undefined) {
    return c.json({ error: 'Campos requeridos: version_id, nro_plaza, campo_modificado, valor_nuevo' }, 400);
  }

  // Obtener valor anterior
  const pos = await c.env.DB.prepare(
    `SELECT ${body.campo_modificado} as val FROM cosper_posiciones WHERE version_id = ? AND nro_plaza = ?`
  ).bind(body.version_id, body.nro_plaza).first<{ val: string }>();

  const valor_anterior = pos?.val ?? null;

  // Registrar override
  await c.env.DB.prepare(`
    INSERT INTO cosper_overrides (version_id, nro_plaza, campo_modificado, valor_anterior, valor_nuevo, razon, usuario)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    body.version_id, body.nro_plaza, body.campo_modificado,
    valor_anterior, body.valor_nuevo,
    body.razon ?? null, body.usuario ?? 'usuario'
  ).run();

  // Aplicar el cambio en la posición
  const campos_permitidos = ['estado', 'sociedad_id', 'tipo_registro', 'puesto', 'ceco_plaza'];
  if (campos_permitidos.includes(body.campo_modificado)) {
    await c.env.DB.prepare(
      `UPDATE cosper_posiciones SET ${body.campo_modificado} = ? WHERE version_id = ? AND nro_plaza = ?`
    ).bind(body.valor_nuevo, body.version_id, body.nro_plaza).run();
  }

  return c.json({ ok: true });
});
```

**Step 4: Actualizar `workers/src/index.ts`** — agregar los nuevos routers:

```typescript
import { syncRouter } from './routers/sync';
import { overridesRouter } from './routers/overrides';
// ... (mantener imports existentes)

app.route(`${BASE}/sync`, syncRouter);
app.route(`${BASE}/overrides`, overridesRouter);
```

**Step 5: Commit**

```bash
git add workers/src/
git commit -m "feat(sync): agregar sync desde Estructura + overrides con audit trail"
```

---

### Task 7: FX Rates + Cost Upload (Excel)

**Files:**
- Create: `workers/src/routers/fx.ts`
- Create: `workers/src/routers/costos.ts`
- Create: `workers/src/services/excel.ts`

**Step 1: Instalar SheetJS**

```bash
cd workers
npm install xlsx
```

**Step 2: Crear `workers/src/services/excel.ts`**

```typescript
import * as XLSX from 'xlsx';

export interface FilaCostoExcel {
  nro_plaza: string;
  sociedad_id: string;
  periodo: string;          // YYYY-MM
  concepto_id: string;
  importe_lc: number;
  headcount?: number;
  tipo_dato: 'real' | 'proyeccion';
}

export interface FilaFXExcel {
  sociedad_id: string;
  periodo: string;          // YYYY-MM
  tasa_lc_por_usd: number;
}

export function parsearExcelCostos(buffer: ArrayBuffer): {
  filas: FilaCostoExcel[];
  errores: string[];
} {
  const workbook = XLSX.read(buffer, { type: 'array' });
  const sheet = workbook.Sheets[workbook.SheetNames[0]!];
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet);

  const filas: FilaCostoExcel[] = [];
  const errores: string[] = [];
  const camposRequeridos = ['nro_plaza', 'sociedad_id', 'periodo', 'concepto_id', 'importe_lc', 'tipo_dato'];

  rows.forEach((row, i) => {
    const fila = i + 2; // Excel rows start at 2 (row 1 is header)
    const faltantes = camposRequeridos.filter(c => !row[c]);
    if (faltantes.length > 0) {
      errores.push(`Fila ${fila}: campos faltantes: ${faltantes.join(', ')}`);
      return;
    }

    const importe = parseFloat(String(row['importe_lc']));
    if (isNaN(importe)) {
      errores.push(`Fila ${fila}: importe_lc inválido: ${row['importe_lc']}`);
      return;
    }

    const tipo_dato = String(row['tipo_dato']);
    if (!['real', 'proyeccion'].includes(tipo_dato)) {
      errores.push(`Fila ${fila}: tipo_dato debe ser 'real' o 'proyeccion', recibido: ${tipo_dato}`);
      return;
    }

    filas.push({
      nro_plaza:   String(row['nro_plaza']),
      sociedad_id: String(row['sociedad_id']),
      periodo:     String(row['periodo']),
      concepto_id: String(row['concepto_id']),
      importe_lc:  importe,
      headcount:   row['headcount'] ? parseFloat(String(row['headcount'])) : 1.0,
      tipo_dato:   tipo_dato as 'real' | 'proyeccion',
    });
  });

  return { filas, errores };
}

export function parsearExcelFX(buffer: ArrayBuffer): {
  filas: FilaFXExcel[];
  errores: string[];
} {
  const workbook = XLSX.read(buffer, { type: 'array' });
  const sheet = workbook.Sheets[workbook.SheetNames[0]!];
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet);

  const filas: FilaFXExcel[] = [];
  const errores: string[] = [];

  rows.forEach((row, i) => {
    const fila = i + 2;
    if (!row['sociedad_id'] || !row['periodo'] || !row['tasa_lc_por_usd']) {
      errores.push(`Fila ${fila}: campos requeridos: sociedad_id, periodo, tasa_lc_por_usd`);
      return;
    }
    const tasa = parseFloat(String(row['tasa_lc_por_usd']));
    if (isNaN(tasa) || tasa <= 0) {
      errores.push(`Fila ${fila}: tasa_lc_por_usd inválida: ${row['tasa_lc_por_usd']}`);
      return;
    }
    filas.push({
      sociedad_id:    String(row['sociedad_id']),
      periodo:        String(row['periodo']),
      tasa_lc_por_usd: tasa,
    });
  });

  return { filas, errores };
}
```

**Step 3: Crear `workers/src/routers/fx.ts`**

```typescript
import { Hono } from 'hono';
import { db } from '../db/queries';
import { parsearExcelFX } from '../services/excel';
import type { Env } from '../types';

export const fxRouter = new Hono<{ Bindings: Env }>();

// GET /api/cosper/v1/fx?version_id=MH_2026&sociedad_id=PE01
fxRouter.get('/', async (c) => {
  const { version_id, sociedad_id } = c.req.query();
  if (!version_id) return c.json({ error: 'Se requiere version_id' }, 400);
  const list = await db.tiposCambio.listByVersion(c.env.DB, version_id, sociedad_id);
  return c.json({ data: list });
});

// POST /api/cosper/v1/fx/upload  (multipart Excel)
fxRouter.post('/upload', async (c) => {
  const formData = await c.req.formData();
  const versionId = formData.get('version_id') as string;
  const file = formData.get('file') as File | null;

  if (!versionId || !file) return c.json({ error: 'Se requiere version_id y file' }, 400);

  const buffer = await file.arrayBuffer();
  const { filas, errores } = parsearExcelFX(buffer);

  if (errores.length > 0 && filas.length === 0) {
    return c.json({ ok: false, errores }, 400);
  }

  await c.env.DB.batch(
    filas.map(f =>
      c.env.DB.prepare(`
        INSERT INTO tipos_cambio (version_id, sociedad_id, periodo, tasa_lc_por_usd)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(version_id, sociedad_id, periodo) DO UPDATE SET tasa_lc_por_usd = excluded.tasa_lc_por_usd
      `).bind(versionId, f.sociedad_id, f.periodo, f.tasa_lc_por_usd)
    )
  );

  return c.json({ ok: true, cargados: filas.length, advertencias: errores.length > 0 ? errores : undefined });
});

// PUT /api/cosper/v1/fx (upsert manual)
fxRouter.put('/', async (c) => {
  const body = await c.req.json<{ version_id: string; sociedad_id: string; periodo: string; tasa_lc_por_usd: number }>();
  await db.tiposCambio.upsert(c.env.DB, body);
  return c.json({ ok: true });
});
```

**Step 4: Crear `workers/src/routers/costos.ts`**

```typescript
import { Hono } from 'hono';
import { parsearExcelCostos } from '../services/excel';
import type { Env } from '../types';

export const costosRouter = new Hono<{ Bindings: Env }>();

// POST /api/cosper/v1/costos/upload (multipart Excel)
costosRouter.post('/upload', async (c) => {
  const formData = await c.req.formData();
  const versionId = formData.get('version_id') as string;
  const file = formData.get('file') as File | null;

  if (!versionId || !file) return c.json({ error: 'Se requiere version_id y file' }, 400);

  const version = await c.env.DB.prepare('SELECT id, estado FROM versiones WHERE id = ?')
    .bind(versionId).first<{ id: string; estado: string }>();
  if (!version) return c.json({ error: 'Versión no encontrada' }, 404);
  if (version.estado === 'oficial') return c.json({ error: 'No se puede cargar datos en una versión oficial' }, 400);

  const buffer = await file.arrayBuffer();
  const { filas, errores } = parsearExcelCostos(buffer);

  if (errores.length > 0 && filas.length === 0) {
    return c.json({ ok: false, errores }, 400);
  }

  // Obtener FX para calcular importe_usd
  const fxRates = await c.env.DB.prepare(
    'SELECT sociedad_id, periodo, tasa_lc_por_usd FROM tipos_cambio WHERE version_id = ?'
  ).bind(versionId).all<{ sociedad_id: string; periodo: string; tasa_lc_por_usd: number }>();

  const fxMap = new Map<string, number>();
  for (const fx of fxRates.results) {
    fxMap.set(`${fx.sociedad_id}|${fx.periodo}`, fx.tasa_lc_por_usd);
  }

  const inserts = filas.map(f => {
    const tasa = fxMap.get(`${f.sociedad_id}|${f.periodo}`);
    const importe_usd = tasa ? f.importe_lc / tasa : null;
    return c.env.DB.prepare(`
      INSERT INTO data_cosper (version_id, nro_plaza, sociedad_id, periodo, concepto_id, importe_lc, importe_usd, headcount, tipo_dato)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(versionId, f.nro_plaza, f.sociedad_id, f.periodo, f.concepto_id,
            f.importe_lc, importe_usd, f.headcount ?? 1.0, f.tipo_dato);
  });

  // D1 batch máximo 100 statements
  for (let i = 0; i < inserts.length; i += 100) {
    await c.env.DB.batch(inserts.slice(i, i + 100));
  }

  return c.json({ ok: true, cargados: filas.length, advertencias: errores.length > 0 ? errores : undefined });
});
```

**Step 5: Actualizar `workers/src/index.ts`**

```typescript
import { fxRouter } from './routers/fx';
import { costosRouter } from './routers/costos';

app.route(`${BASE}/fx`, fxRouter);
app.route(`${BASE}/costos`, costosRouter);
```

**Step 6: Commit**

```bash
git add workers/src/
git commit -m "feat(upload): agregar carga de FX rates y costos desde Excel (SheetJS)"
```

---

### Task 8: Router de Análisis FX

**Files:**
- Create: `workers/src/routers/analisis.ts`
- Modify: `workers/src/index.ts`

**Step 1: Crear `workers/src/routers/analisis.ts`**

```typescript
import { Hono } from 'hono';
import { db } from '../db/queries';
import { calcularAnalisisFX, calcularAnalisisFXAgregado } from '../services/fx_calculator';
import type { Env } from '../types';

export const analisisRouter = new Hono<{ Bindings: Env }>();

// GET /api/cosper/v1/analisis
// Query: version_base, version_comp, sociedad_id?, periodo?, periodo_hasta?, agrupacion?
analisisRouter.get('/', async (c) => {
  const { version_base, version_comp, sociedad_id, periodo, periodo_hasta, agrupacion } = c.req.query();

  if (!version_base || !version_comp) {
    return c.json({ error: 'Se requieren version_base y version_comp' }, 400);
  }

  const rawData = await db.dataCosper.getAnalisis(
    c.env.DB, version_base, version_comp,
    { sociedad_id, periodo, periodo_hasta }
  );

  // Aplicar descomposición FX fila por fila
  const filas = rawData.results.map((row: any) => {
    const fx = calcularAnalisisFX({
      presupuesto_lc: row.ppto_lc ?? 0,
      real_lc: row.real_lc ?? 0,
      fx_presupuesto: row.fx_ppto ?? 1,
      fx_real: row.fx_real ?? 1,
    });
    return {
      sociedad_id:     row.sociedad_id,
      pais:            row.pais,
      moneda_local:    row.moneda_local,
      periodo:         row.periodo,
      concepto_id:     row.concepto_id,
      ppto_lc:         row.ppto_lc ?? 0,
      real_lc:         row.real_lc ?? 0,
      fx_presupuesto:  row.fx_ppto ?? null,
      fx_real:         row.fx_real ?? null,
      ...fx,
    };
  });

  // Aggregación opcional
  if (agrupacion === 'pais') {
    return c.json({ data: agruparPorPais(filas), version_base, version_comp });
  }
  if (agrupacion === 'sociedad') {
    return c.json({ data: agruparPorSociedad(filas), version_base, version_comp });
  }

  return c.json({ data: filas, version_base, version_comp, total_filas: filas.length });
});

// ── Helpers de agrupación ────────────────────────────────────────────────────

function agruparPorPais(filas: any[]) {
  const mapa = new Map<string, any[]>();
  for (const f of filas) {
    const key = f.pais;
    if (!mapa.has(key)) mapa.set(key, []);
    mapa.get(key)!.push(f);
  }
  return Array.from(mapa.entries()).map(([pais, rows]) => {
    const agregado = calcularAnalisisFXAgregado(rows.map(r => ({
      presupuesto_lc: r.ppto_lc, real_lc: r.real_lc,
      fx_presupuesto: r.fx_presupuesto ?? 1, fx_real: r.fx_real ?? 1,
    })));
    return { pais, sociedades: [...new Set(rows.map((r: any) => r.sociedad_id))], ...agregado };
  });
}

function agruparPorSociedad(filas: any[]) {
  const mapa = new Map<string, any[]>();
  for (const f of filas) {
    const key = `${f.sociedad_id}`;
    if (!mapa.has(key)) mapa.set(key, []);
    mapa.get(key)!.push(f);
  }
  return Array.from(mapa.entries()).map(([sociedad_id, rows]) => {
    const agregado = calcularAnalisisFXAgregado(rows.map(r => ({
      presupuesto_lc: r.ppto_lc, real_lc: r.real_lc,
      fx_presupuesto: r.fx_presupuesto ?? 1, fx_real: r.fx_real ?? 1,
    })));
    return { sociedad_id, pais: rows[0]?.pais, moneda_local: rows[0]?.moneda_local, ...agregado };
  });
}
```

**Step 2: Agregar a `workers/src/index.ts`**

```typescript
import { analisisRouter } from './routers/analisis';
app.route(`${BASE}/analisis`, analisisRouter);
```

**Step 3: Probar el endpoint**

```bash
# Con datos de prueba cargados en dev local:
curl "http://localhost:8787/api/cosper/v1/analisis?version_base=MH_2026&version_comp=M01_2026&agrupacion=pais"
```

**Step 4: Commit**

```bash
git add workers/src/
git commit -m "feat(analisis): agregar endpoint de análisis FX con 3 capas y agregaciones"
```

---

## Fase 4: Actualizar b-connect-plus

### Task 9: Agregar ruta /cosper al gateway

**Files:**
- Modify: `../b-connect-plus/workers/src/types.ts`
- Modify: `../b-connect-plus/workers/src/index.ts`
- Modify: `../b-connect-plus/workers/wrangler.toml`

**Step 1: Modificar `types.ts` en b-connect-plus**

Agregar `COSPER_SERVICE`:

```typescript
export interface Env {
  ESTRUCTURA_SERVICE: Fetcher;
  COSPER_SERVICE: Fetcher;    // ← nuevo
  BASE_PATH: string;
}
```

**Step 2: Modificar `index.ts` en b-connect-plus**

Agregar función y rutas:

```typescript
// Junto a forwardToEstructura
async function forwardToCosper(c: Context<{ Bindings: Env }>) {
  return c.env.COSPER_SERVICE.fetch(c.req.raw);
}

// Rutas cosper
app.all('/cosper/*', forwardToCosper);
app.all('/api/cosper/*', forwardToCosper);
```

**Step 3: Modificar `wrangler.toml` en b-connect-plus**

En `[services]` del staging:
```toml
{ binding = "COSPER_SERVICE", service = "belcorp-cosper-api-staging" }
```

En `[[env.production.services]]`:
```toml
{ binding = "COSPER_SERVICE", service = "belcorp-cosper-api" }
```

**Step 4: Commit en b-connect-plus**

```bash
cd ../b-connect-plus/workers
git add src/ wrangler.toml
git commit -m "feat: agregar Service Binding y rutas para cosper Worker"
```

---

## Fase 5: Frontend React

### Task 10: Inicializar proyecto React + Vite

**Files:**
- Create: `frontend/` (todo el proyecto)

**Step 1: Inicializar Vite**

```bash
cd frontend
npm create vite@latest app -- --template react-ts
cd app
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install react-router-dom @tanstack/react-query recharts
```

**Step 2: Configurar `frontend/app/vite.config.ts`**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/cosper/',
  server: {
    host: true,
    port: 5175,
    allowedHosts: ['belcorp.paulrojasj.com', 'localhost'],
    proxy: {
      '/api/cosper': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
        secure: false,
      }
    }
  },
});
```

**Step 3: Configurar `frontend/app/.env`**

```env
VITE_API_URL=/api/cosper/v1
```

**Step 4: Crear `frontend/app/src/api/client.ts`**

```typescript
const BASE = import.meta.env.VITE_API_URL ?? '/api/cosper/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error((err as any).error ?? resp.statusText);
  }
  return resp.json();
}

export const api = {
  sociedades: {
    list: () => request<{ data: any[] }>('/sociedades'),
  },
  versiones: {
    list: (anio?: number) => request<{ data: any[] }>(`/versiones${anio ? `?anio=${anio}` : ''}`),
    cerrar: (id: string) => request(`/versiones/${id}/cerrar`, { method: 'POST' }),
  },
  analisis: {
    get: (params: Record<string, string>) =>
      request<{ data: any[] }>(`/analisis?${new URLSearchParams(params)}`),
  },
  sync: {
    ejecutar: (version_id: string, fecha: string) =>
      request('/sync', { method: 'POST', body: JSON.stringify({ version_id, fecha }) }),
    posiciones: (version_id: string, sociedad_id?: string) =>
      request<{ data: any[] }>(`/sync/posiciones?version_id=${version_id}${sociedad_id ? `&sociedad_id=${sociedad_id}` : ''}`),
  },
  fx: {
    list: (version_id: string, sociedad_id?: string) =>
      request<{ data: any[] }>(`/fx?version_id=${version_id}${sociedad_id ? `&sociedad_id=${sociedad_id}` : ''}`),
    upsert: (data: any) => request('/fx', { method: 'PUT', body: JSON.stringify(data) }),
  },
};
```

**Step 5: Actualizar `frontend/app/src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';
import { Sociedad } from './pages/Sociedad';
import { Upload } from './pages/Upload';
import { Versiones } from './pages/Versiones';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/cosper">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sociedad/:id" element={<Sociedad />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/versiones" element={<Versiones />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

**Step 6: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): inicializar React + Vite + Tailwind + React Query"
```

---

### Task 11: Componente FXAnalysisTable (el core del dashboard)

**Files:**
- Create: `frontend/app/src/components/FXAnalysisTable.tsx`
- Create: `frontend/app/src/pages/Dashboard.tsx`

**Step 1: Crear `frontend/app/src/components/FXAnalysisTable.tsx`**

```tsx
interface FXRow {
  sociedad_id?: string;
  pais?: string;
  concepto_id?: string;
  periodo?: string;
  ppto_lc?: number;
  real_lc?: number;
  presupuesto_usd: number;
  real_usd: number;
  variacion_lc: number;
  efecto_fx: number;
  variacion_total_usd: number;
  variacion_real_negocio_usd: number;
}

interface Props {
  data: FXRow[];
  modo: 'pais' | 'sociedad' | 'concepto';
}

function fmt(n: number, decimals = 0) {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n);
}

function badge(n: number) {
  const cls = n > 0 ? 'text-red-600' : n < 0 ? 'text-green-600' : 'text-gray-400';
  const sign = n > 0 ? '+' : '';
  return <span className={`font-semibold ${cls}`}>{sign}{fmt(n, 0)}</span>;
}

export function FXAnalysisTable({ data, modo }: Props) {
  const labelKey = modo === 'pais' ? 'pais' : modo === 'sociedad' ? 'sociedad_id' : 'concepto_id';

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
      <table className="min-w-full text-sm">
        <thead className="bg-[#672779] text-white">
          <tr>
            <th className="px-4 py-3 text-left">
              {modo === 'pais' ? 'País' : modo === 'sociedad' ? 'Sociedad' : 'Concepto'}
            </th>
            <th className="px-4 py-3 text-right">Presupuesto USD</th>
            <th className="px-4 py-3 text-right">Real/Proy USD</th>
            <th className="px-4 py-3 text-right border-l-2 border-purple-300">
              Var. Total USD
            </th>
            <th className="px-4 py-3 text-right bg-purple-900/20">
              Efecto FX
            </th>
            <th className="px-4 py-3 text-right">
              Var. Real Negocio
            </th>
            <th className="px-4 py-3 text-right border-l-2 border-purple-300">
              Var. LC (gestión)
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.map((row, i) => (
            <tr key={i} className="hover:bg-purple-50 transition-colors">
              <td className="px-4 py-3 font-medium text-gray-800">
                {(row as any)[labelKey] ?? '—'}
              </td>
              <td className="px-4 py-3 text-right text-gray-600">
                ${fmt(row.presupuesto_usd)}
              </td>
              <td className="px-4 py-3 text-right text-gray-600">
                ${fmt(row.real_usd)}
              </td>
              <td className="px-4 py-3 text-right border-l-2 border-purple-100 font-semibold">
                {badge(row.variacion_total_usd)}
              </td>
              <td className="px-4 py-3 text-right bg-purple-50/50 text-xs text-gray-500">
                {badge(row.efecto_fx)}
              </td>
              <td className="px-4 py-3 text-right">
                {badge(row.variacion_real_negocio_usd)}
              </td>
              <td className="px-4 py-3 text-right border-l-2 border-purple-100 text-xs text-gray-500">
                {badge(row.variacion_lc)}
              </td>
            </tr>
          ))}
        </tbody>
        {data.length > 1 && (
          <tfoot className="bg-gray-50 font-bold border-t-2 border-gray-300">
            <tr>
              <td className="px-4 py-3">TOTAL</td>
              <td className="px-4 py-3 text-right">${fmt(data.reduce((s,r) => s + r.presupuesto_usd, 0))}</td>
              <td className="px-4 py-3 text-right">${fmt(data.reduce((s,r) => s + r.real_usd, 0))}</td>
              <td className="px-4 py-3 text-right border-l-2 border-purple-100">
                {badge(data.reduce((s,r) => s + r.variacion_total_usd, 0))}
              </td>
              <td className="px-4 py-3 text-right bg-purple-50/50">
                {badge(data.reduce((s,r) => s + r.efecto_fx, 0))}
              </td>
              <td className="px-4 py-3 text-right">
                {badge(data.reduce((s,r) => s + r.variacion_real_negocio_usd, 0))}
              </td>
              <td className="px-4 py-3 text-right border-l-2 border-purple-100">
                {badge(data.reduce((s,r) => s + r.variacion_lc, 0))}
              </td>
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}
```

**Step 2: Crear `frontend/app/src/pages/Dashboard.tsx`**

```tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { FXAnalysisTable } from '../components/FXAnalysisTable';

export function Dashboard() {
  const [versionBase, setVersionBase] = useState('MH_2026');
  const [versionComp, setVersionComp] = useState('M01_2026');
  const [agrupacion, setAgrupacion] = useState<'pais' | 'sociedad'>('pais');

  const { data: versiones } = useQuery({
    queryKey: ['versiones'],
    queryFn: () => api.versiones.list(2026),
  });

  const { data: analisis, isLoading } = useQuery({
    queryKey: ['analisis', versionBase, versionComp, agrupacion],
    queryFn: () => api.analisis.get({ version_base: versionBase, version_comp: versionComp, agrupacion }),
    enabled: !!versionBase && !!versionComp,
  });

  const versionList = versiones?.data ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-[#3D1550] to-[#8B3A9E] text-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">COSPER — Costo de Personal</h1>
            <p className="text-purple-200 text-sm">Belcorp · Control Presupuestario</p>
          </div>
          <nav className="flex gap-4 text-sm">
            <a href="/cosper/versiones" className="hover:text-purple-200">Versiones</a>
            <a href="/cosper/upload" className="hover:text-purple-200">Carga de datos</a>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Controles */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap gap-4 items-center">
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-1">Versión base</label>
            <select
              value={versionBase}
              onChange={e => setVersionBase(e.target.value)}
              className="border rounded-lg px-3 py-1.5 text-sm"
            >
              {versionList.map((v: any) => (
                <option key={v.id} value={v.id}>{v.nombre}</option>
              ))}
            </select>
          </div>
          <span className="text-gray-400 text-lg mt-4">vs</span>
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-1">Comparar con</label>
            <select
              value={versionComp}
              onChange={e => setVersionComp(e.target.value)}
              className="border rounded-lg px-3 py-1.5 text-sm"
            >
              {versionList.map((v: any) => (
                <option key={v.id} value={v.id}>{v.nombre}</option>
              ))}
            </select>
          </div>
          <div className="ml-auto">
            <label className="text-xs font-medium text-gray-500 block mb-1">Agrupar por</label>
            <div className="flex rounded-lg overflow-hidden border border-gray-200">
              {(['pais', 'sociedad'] as const).map(g => (
                <button
                  key={g}
                  onClick={() => setAgrupacion(g)}
                  className={`px-3 py-1.5 text-sm capitalize ${agrupacion === g ? 'bg-[#672779] text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                >
                  {g === 'pais' ? 'País' : 'Sociedad'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tabla principal */}
        {isLoading ? (
          <div className="text-center py-12 text-gray-400">Cargando análisis...</div>
        ) : analisis?.data?.length ? (
          <FXAnalysisTable data={analisis.data} modo={agrupacion} />
        ) : (
          <div className="text-center py-12 text-gray-400">
            No hay datos para las versiones seleccionadas.
          </div>
        )}
      </main>
    </div>
  );
}
```

**Step 3: Correr el frontend**

```bash
cd frontend/app
npm run dev
```

Abrir `http://localhost:5175/cosper/` — debe mostrar el dashboard con los controles de versión.

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat(ui): agregar Dashboard con FXAnalysisTable y selectores de versión"
```

---

## Fase 6: Deployment

### Task 12: Deploy Worker + D1 + b-connect-plus

**Step 1: Crear D1 de producción**

```powershell
cd workers
./node_modules/.bin/wrangler d1 create cosper-db
# Copiar el database_id y actualizar PLACEHOLDER_PROD en wrangler.toml
```

**Step 2: Aplicar migraciones en producción**

```powershell
./node_modules/.bin/wrangler d1 execute cosper-db --env production --file=migrations/0001_initial.sql
./node_modules/.bin/wrangler d1 execute cosper-db --env production --file=migrations/0002_seed.sql
```

**Step 3: Deploy del Worker**

```powershell
./node_modules/.bin/wrangler deploy --env production
```

Esperado: `✅ Deployed belcorp-cosper-api`

**Step 4: Build y deploy del frontend (desde el Worker)**

```bash
cd frontend/app
node node_modules/vite/bin/vite.js build
```

Los assets generados se sirven desde el Worker (ver Task 13).

**Step 5: Deploy del gateway b-connect-plus**

```powershell
cd ../b-connect-plus/workers
./node_modules/.bin/wrangler deploy --env production
```

**Step 6: Verificar**

```bash
# Health
curl https://belcorp.paulrojasj.com/api/cosper/health

# Frontend
# Abrir: https://belcorp.paulrojasj.com/cosper/
```

**Step 7: Commit final de configuración**

```bash
git add workers/wrangler.toml
git commit -m "deploy: actualizar wrangler.toml con database IDs de producción"
```

---

### Task 13: Servir SPA desde el Worker

**Files:**
- Modify: `workers/wrangler.toml` — agregar assets binding
- Modify: `workers/src/index.ts` — servir SPA

**Step 1: Actualizar `workers/wrangler.toml`** para servir los assets del frontend

```toml
[assets]
directory = "../frontend/app/dist"
```

**Step 2: Actualizar `workers/src/index.ts`** — fallback para SPA

```typescript
// Al final del router, antes de export default:
// Todas las rutas no-API que no matcheen sirven el index.html de la SPA
app.get('/cosper/*', async (c) => {
  // Cloudflare Assets maneja esto automáticamente con [assets] en wrangler.toml
  return c.env.ASSETS?.fetch(c.req.raw) ?? new Response('Not found', { status: 404 });
});
```

Y en `types.ts`:
```typescript
export interface Env {
  DB: D1Database;
  ESTRUCTURA_SERVICE: Fetcher;
  BASE_PATH: string;
  ASSETS: Fetcher;   // ← para servir la SPA
}
```

**Step 3: Rebuild y redeploy**

```powershell
cd frontend/app
node node_modules/vite/bin/vite.js build

cd ../../workers
./node_modules/.bin/wrangler deploy --env production
```

**Step 4: Commit**

```bash
git add .
git commit -m "feat: servir SPA React desde el Worker via Cloudflare Assets"
```

---

## Resumen de Endpoints MVP

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/cosper/health` | Health check |
| GET/POST | `/api/cosper/v1/sociedades` | CRUD sociedades |
| GET/POST | `/api/cosper/v1/versiones` | CRUD versiones |
| POST | `/api/cosper/v1/versiones/:id/cerrar` | Cerrar versión (read-only) |
| POST | `/api/cosper/v1/sync` | Sync headcount desde Estructura |
| GET | `/api/cosper/v1/sync/posiciones` | Ver posiciones sincronizadas |
| GET/POST | `/api/cosper/v1/overrides` | Ver/crear overrides con audit trail |
| GET/POST/PUT | `/api/cosper/v1/fx` | Tipos de cambio |
| POST | `/api/cosper/v1/fx/upload` | Upload Excel FX |
| POST | `/api/cosper/v1/costos/upload` | Upload Excel costos |
| GET | `/api/cosper/v1/analisis` | Análisis FX 3 capas |

## Templates Excel Requeridos

Crear en `docs/templates/`:

**`costos_template.xlsx`** columnas:
`nro_plaza | sociedad_id | periodo (YYYY-MM) | concepto_id | importe_lc | headcount | tipo_dato (real/proyeccion)`

**`fx_template.xlsx`** columnas:
`sociedad_id | periodo (YYYY-MM) | tasa_lc_por_usd`
