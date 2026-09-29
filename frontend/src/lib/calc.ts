/**
 * Frontend mirror of the Python calculation engine (backend/app/engine/*).
 *
 * GOLDEN RULES honored here:
 * - Decimal arithmetic ONLY (decimal.js) — never JS Number for pass/fail.
 * - Base unit = gram internally; instrument values converted at the boundary.
 * - The BACKEND remains the source of truth: it recomputes and persists the
 *   authoritative verdict. This mirror exists purely for live preview.
 *
 * Mirrors: units.py, classification.py, mpe.py, error.py, validate.py,
 * suggest_loads.py — keep in sync with rulesets/oiml-r76-2006.json.
 */
import Decimal from 'decimal.js';

Decimal.set({ precision: 34, toExpNeg: -21, toExpPos: 21 });

export type D = Decimal;
export type AccuracyClass = 'I' | 'II' | 'III' | 'IIII';
export type MpeContext = 'INITIAL' | 'IN_SERVICE';

export const dec = (v: string | number): D => new Decimal(v);

export const UNIT_TO_GRAM: Record<string, D> = {
  mg: dec('0.001'),
  g: dec(1),
  kg: dec(1000),
  t: dec('1000000'),
  ct: dec('0.2'),
};

export function toBase(value: string, unit: string): D {
  const f = UNIT_TO_GRAM[unit];
  if (!f) throw new Error(`Unknown unit: ${unit}`);
  return dec(value).times(f);
}

export function fromBase(grams: D, unit: string): D {
  const f = UNIT_TO_GRAM[unit];
  if (!f) throw new Error(`Unknown unit: ${unit}`);
  return grams.div(f);
}

/** Parse a user-entered decimal string; null when empty/invalid. */
export function pd(s: string | null | undefined): D | null {
  if (s === null || s === undefined) return null;
  const t = s.trim();
  if (!t) return null;
  try {
    const d = new Decimal(t);
    return d.isFinite() ? d : null;
  } catch {
    return null;
  }
}

/** Format grams into the working unit for display. */
export function fmtU(grams: D | null | undefined, unit: string): string {
  if (grams === null || grams === undefined) return '—';
  return fromBase(grams, unit).toString();
}

// ─────────────────────────────────────────────── ruleset mirror (r76-2006.json)

/** R 76-1 Table 6 [V] — boundary INCLUSIVE (m ≤ up_to → this band). */
export const MPE_BANDS: Record<AccuracyClass, { upTo: string | null; mult: string }[]> = {
  I: [
    { upTo: '50000', mult: '0.5' },
    { upTo: '200000', mult: '1.0' },
    { upTo: null, mult: '1.5' },
  ],
  II: [
    { upTo: '5000', mult: '0.5' },
    { upTo: '20000', mult: '1.0' },
    { upTo: null, mult: '1.5' },
  ],
  III: [
    { upTo: '500', mult: '0.5' },
    { upTo: '2000', mult: '1.0' },
    { upTo: null, mult: '1.5' },
  ],
  IIII: [
    { upTo: '50', mult: '0.5' },
    { upTo: '200', mult: '1.0' },
    { upTo: null, mult: '1.5' },
  ],
};

const IN_SERVICE_MULT = dec(2); // 3.5.2 [V]

/** R 76-1 Table 3 [V] — e bands in GRAMS, n limits, Min in e. */
export const TABLE3: Record<
  AccuracyClass,
  { eMinG: string; eMaxG: string | null; nMin: string; nMax: string | null; minInE: string }[]
> = {
  I: [{ eMinG: '0.001', eMaxG: null, nMin: '50000', nMax: null, minInE: '100' }],
  II: [
    { eMinG: '0.001', eMaxG: '0.05', nMin: '100', nMax: '100000', minInE: '20' },
    { eMinG: '0.1', eMaxG: null, nMin: '5000', nMax: '100000', minInE: '50' },
  ],
  III: [
    { eMinG: '0.1', eMaxG: '2', nMin: '100', nMax: '10000', minInE: '20' },
    { eMinG: '5', eMaxG: null, nMin: '500', nMax: '10000', minInE: '20' },
  ],
  IIII: [{ eMinG: '5', eMaxG: null, nMin: '100', nMax: '1000', minInE: '10' }],
};

// ───────────────────────────────────────────── classification.py mirror

export interface EngineRange {
  idx: number;
  e: D;
  d: D;
  max: D;
  min: D; // Min_i = Max_(i-1) [V 3.3]
}

export interface EngineInstrument {
  cls: AccuracyClass;
  ranges: EngineRange[];
  minCap: D;
  tarePlus: D;
  max: D;
  isMultiInterval: boolean;
  smallestE: D;
  rangeForLoad(loadG: D): EngineRange; // throws when load > Max
}

export function buildEngineInstrument(
  cls: AccuracyClass,
  minCapacity: string,
  unit: string,
  ranges: { e: string; d: string; max: string }[],
): EngineInstrument {
  if (ranges.length === 0) throw new Error('At least one range is required');
  const minG = toBase(minCapacity, unit);
  const conv = ranges.map((r) => ({
    e: toBase(r.e, unit),
    d: toBase(r.d, unit),
    max: toBase(r.max, unit),
  }));
  const built: EngineRange[] = conv.map((r, i) => ({
    idx: i + 1,
    e: r.e,
    d: r.d,
    max: r.max,
    min: i === 0 ? minG : conv[i - 1].max,
  }));

  const inst: EngineInstrument = {
    cls,
    ranges: built,
    minCap: minG,
    tarePlus: dec(0),
    max: built[built.length - 1].max,
    isMultiInterval: built.length > 1,
    smallestE: built[0].e,
    rangeForLoad(loadG: D): EngineRange {
      for (const r of built) if (loadG.lte(r.max)) return r;
      throw new Error(`Load ${loadG.toString()} g exceeds Max ${inst.max.toString()} g`);
    },
  };
  return inst;
}

// ──────────────────────────────────────────────────────── mpe.py mirror

function bandMultiplier(cls: AccuracyClass, mInE: D): D {
  for (const b of MPE_BANDS[cls]) {
    if (b.upTo === null || mInE.lte(dec(b.upTo))) return dec(b.mult);
  }
  throw new Error(`Load ${mInE.toString()} e is beyond Table 6 for class ${cls}`);
}

export function mpeOf(inst: EngineInstrument, loadG: D, context: MpeContext = 'INITIAL'): D {
  if (loadG.isNeg()) throw new Error('Load cannot be negative');
  const r = inst.rangeForLoad(loadG);
  const mult = bandMultiplier(inst.cls, loadG.div(r.e));
  let v = mult.times(r.e);
  if (context === 'IN_SERVICE') v = v.times(IN_SERVICE_MULT);
  return v;
}

// ─────────────────────────────────────────────────────── error.py mirror

export interface PointResult {
  P: D;
  E: D;
}

/** P = I + ½·step − ΔL (changeover method [V]); E = P − L. */
export function pointError(
  I: D,
  L: D,
  dL: D | null,
  step: D,
  method: 'changeover' | 'direct' = 'changeover',
): PointResult {
  const P =
    method === 'direct' ? I : I.plus(step.div(2)).minus(dL === null ? dec(0) : dL);
  return { P, E: P.minus(L) };
}

export const passes = (Ec: D, mpe: D): boolean => Ec.abs().lte(mpe.abs());

export interface ZeroRowIn {
  L: string;
  I: string;
  dL: string;
}

/** E0 from the near-zero row; null when the row has no indication. */
export function zeroErrorG(zero: ZeroRowIn | null | undefined, stepG: D): D | null {
  if (!zero) return null;
  const I = pd(zero.I);
  if (I === null) return null;
  const L = pd(zero.L) ?? dec(0);
  const dL = pd(zero.dL) ?? dec(0);
  return pointError(I, L, dL, stepG).E;
}

// ─────────────────────────────────────────────── weighing live evaluation

export interface WeighingCell {
  E: D;
  Ec: D;
  pass: boolean;
}

export interface WeighingRowLive {
  L: D;
  mpe: D | null;
  up: WeighingCell | null;
  down: WeighingCell | null;
}

export interface WeighingLive {
  e0: D | null;
  rows: WeighingRowLive[];
  anyObs: boolean;
  allPass: boolean;
  anyFail: boolean;
}

export interface DirectionIn {
  I: string;
  dL: string;
}

export interface PointRowIn {
  L: string;
  up: DirectionIn;
  down: DirectionIn;
}

export interface WeighingObs {
  zero?: ZeroRowIn | null;
  points?: PointRowIn[] | null;
}

export function evaluateWeighingLive(
  obs: WeighingObs,
  inst: EngineInstrument,
  mpeContext: MpeContext,
  resolutionG: D | null,
): WeighingLive {
  const step0 = resolutionG ?? inst.ranges[0].d;
  const e0 = zeroErrorG(obs.zero, step0) ?? dec(0);
  const rows: WeighingRowLive[] = [];
  let anyObs = false;
  let allPass = true;
  let anyFail = false;

  for (const p of obs.points ?? []) {
    const L = pd(p.L);
    if (L === null) continue;
    let m: D | null = null;
    let step: D;
    try {
      m = mpeOf(inst, L, mpeContext);
      step = resolutionG ?? inst.rangeForLoad(L).d;
    } catch {
      step = resolutionG ?? inst.ranges[inst.ranges.length - 1].d;
    }
    const row: WeighingRowLive = { L, mpe: m, up: null, down: null };
    for (const dirn of ['up', 'down'] as const) {
      const I = pd(p[dirn].I);
      if (I === null) continue;
      anyObs = true;
      const dL = pd(p[dirn].dL);
      const { E } = pointError(I, L, dL, step);
      const Ec = E.minus(e0);
      const pass = m !== null ? passes(Ec, m) : false;
      const cell: WeighingCell = { E, Ec, pass };
      row[dirn] = cell;
      if (m !== null) {
        if (pass) allPass = allPass && true;
        else {
          allPass = false;
          anyFail = true;
        }
      }
    }
    rows.push(row);
  }
  return { e0: obs.zero && pd(obs.zero.I) !== null ? e0 : null, rows, anyObs, allPass, anyFail };
}

// ───────────────────────────────────────────── suggest_loads.py mirror

export function suggestLoadsG(inst: EngineInstrument, nMin = 10, blankingAtMax = false): D[] {
  const eLast = inst.ranges[inst.ranges.length - 1].e;
  const loads: D[] = [];
  const push = (x: D) => {
    if (!loads.some((l) => l.eq(x))) loads.push(x);
  };
  push(inst.minCap);
  for (const r of inst.ranges) {
    for (const b of MPE_BANDS[inst.cls]) {
      if (b.upTo !== null) {
        const x = dec(b.upTo).times(r.e);
        if (r.min.lt(x) && r.max.gte(x)) push(x); // MPE change point [V]
      }
    }
    if (r.idx < inst.ranges.length) push(r.max.minus(dec(5).times(r.e))); // 5e below change
  }
  push(inst.max.minus(blankingAtMax ? dec(5).times(eLast) : dec(0)));
  while (loads.length < nMin) {
    const s = [...loads].sort((a, b) => a.comparedTo(b));
    let lo = s[0];
    let hi = s[s.length - 1];
    let gap: D | null = null;
    for (let i = 0; i < s.length - 1; i++) {
      const g = s[i + 1].minus(s[i]);
      if (gap === null || g.gt(gap)) {
        lo = s[i];
        hi = s[i + 1];
        gap = g;
      }
    }
    if (gap === null || gap.isZero()) break;
    push(lo.plus(hi).div(2));
  }
  return loads.sort((a, b) => a.comparedTo(b));
}

// ───────────────────────────────────────────── validate.py mirror (Table 3)

export interface ValidationIssue {
  code: string;
  message: string;
}

function mantissaOf(d: D): number {
  let m = d.abs();
  if (m.isZero()) return 0;
  while (m.lt(1)) m = m.times(10);
  while (m.gte(10)) m = m.div(10);
  return m.toSignificantDigits(6).toNumber();
}

export function validateInstrumentLive(
  cls: AccuracyClass,
  minCapacity: string,
  unit: string,
  ranges: { e: string; d: string; max: string }[],
): { errors: ValidationIssue[]; warnings: ValidationIssue[] } {
  const errors: ValidationIssue[] = [];
  const warnings: ValidationIssue[] = [];
  try {
    const inst = buildEngineInstrument(cls, minCapacity, unit, ranges);

    let prev: D | null = null;
    inst.ranges.forEach((r, i) => {
      const idx = i + 1;
      if (prev !== null && r.e.lte(prev)) {
        errors.push({
          code: 'T3_E_ORDER',
          message: `Range ${idx}: e must increase (3.3) — got ${fmtU(r.e, unit)} ${unit}`,
        });
      }
      prev = r.e;

      const eG = r.e; // already grams
      const row = TABLE3[cls].find(
        (t) =>
          eG.gte(dec(t.eMinG)) && (t.eMaxG === null || eG.lte(dec(t.eMaxG))),
      );
      if (!row) {
        errors.push({
          code: 'T3_E_BAND',
          message: `Range ${idx}: e = ${fmtU(r.e, unit)} ${unit} is outside every Table 3 band for class ${cls}`,
        });
        return;
      }
      const n = r.max.div(r.e);
      const nMin = dec(row.nMin);
      const nMax = row.nMax !== null ? dec(row.nMax) : null;
      if (n.lt(nMin) || (nMax !== null && n.gt(nMax))) {
        errors.push({
          code: 'T3_N',
          message: `Range ${idx}: n = Max/e = ${n.toString()} — allowed ${row.nMin}…${row.nMax ?? '∞'} (Table 3, class ${cls})`,
        });
      }
      if (mantissaOf(r.d) !== 1 && mantissaOf(r.d) !== 2 && mantissaOf(r.d) !== 5) {
        warnings.push({
          code: 'D_FORM',
          message: `Range ${idx}: d = ${fmtU(r.d, unit)} ${unit} is not (1, 2 or 5) × 10^k [checklist 4.2.2.1]`,
        });
      }
    });

    const row1 = TABLE3[cls].find((t) => {
      const eG = inst.ranges[0].e;
      return eG.gte(dec(t.eMinG)) && (t.eMaxG === null || eG.lte(dec(t.eMaxG)));
    });
    if (row1) {
      const minLimit = dec(row1.minInE).times(inst.ranges[0].e);
      if (inst.minCap.lt(minLimit)) {
        errors.push({
          code: 'T3_MIN',
          message: `Min (${fmtU(inst.minCap, unit)} ${unit}) < ${row1.minInE} × e1 = ${fmtU(minLimit, unit)} ${unit}`,
        });
      }
    }
  } catch (e) {
    errors.push({ code: 'PARSE', message: e instanceof Error ? e.message : 'Invalid numbers' });
  }
  return { errors, warnings };
}