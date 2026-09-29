import { useMemo, useState } from 'react';
import type { Decimal } from 'decimal.js';
import { fmtU, mpeOf, passes, pd, pointError, zeroErrorG } from '../../lib/calc';
import { Button } from '../../components/ui/Button';
import { PassFailBadge } from '../../components/data-display/PassFailBadge';
import type { TestFormProps } from './types';

// ─────────────────────────────────────────────── Form 6.1 — Zero return
export function ZeroReturnForm({ instrument, engineInst, resolutionG, existing, readOnly, onSubmit }: TestFormProps) {
  const unit = instrument.unit;
  const obs0 = (existing?.observations ?? {}) as {
    P0?: { L: string; I: string; dL: string };
    P30?: { L: string; I: string; dL: string };
  };
  const [P0, setP0] = useState(obs0.P0 ?? { L: '0', I: '', dL: '' });
  const [P30, setP30] = useState(obs0.P30 ?? { L: '0', I: '', dL: '' });
  const [busy, setBusy] = useState(false);

  const live = useMemo(() => {
    const step = resolutionG ?? engineInst.ranges[0].d;
    const p0 = zeroErrorG(P0, step);
    const p30 = zeroErrorG(P30, step);
    if (p0 === null || p30 === null) return null;
    const change = p30.minus(p0);
    const limit = engineInst.smallestE.times(0.5); // 0.5 e1 [V]
    return { change, limit, pass: passes(change, limit) };
  }, [P0, P30, engineInst, resolutionG]);

  const block = (label: string, val: { L: string; I: string; dL: string }, set: (v: { L: string; I: string; dL: string }) => void) => (
    <div>
      <p className="mb-2 text-sm font-semibold text-slate-700">{label}</p>
      <div className="flex gap-3">
        {(['L', 'I', 'dL'] as const).map((f) => (
          <label key={f} className="text-xs text-slate-600">
            {f}
            <input value={val[f]} disabled={readOnly} inputMode="decimal"
              onChange={(e) => set({ ...val, [f]: e.target.value })}
              className="mt-1 block w-24 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" />
          </label>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm ring-1 ring-inset ring-slate-200">
        Pass: |P₃₀ − P₀| ≤ 0.5 e₁ (A.4.11.2)
      </div>
      <div className="flex flex-wrap gap-8">
        {block('P₀ (before 30-min load)', P0, setP0)}
        {block('P₃₀ (after load removed)', P30, setP30)}
      </div>
      <p className="text-sm">
        Change = <b className={`font-mono ${live ? (live.pass ? 'text-emerald-700' : 'text-red-700') : ''}`}>
          {live ? `${fmtU(live.change, unit)} ${unit}` : '—'}
        </b>{' '}
        · limit <b className="font-mono">{fmtU(live?.limit ?? null, unit)} {unit}</b>{' '}
        <PassFailBadge pass={live?.pass ?? null} />
      </p>
      {!readOnly && (
        <Button loading={busy} onClick={async () => { setBusy(true); try { await onSubmit({ P0, P30 }); } finally { setBusy(false); } }}>
          Save zero-return test
        </Button>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────── Form 6.2 — Creep
interface CreepReading { t_min: string; I: string; dL: string }

export function CreepForm({ instrument, engineInst, resolutionG, mpeContext, existing, readOnly, onSubmit }: TestFormProps) {
  const unit = instrument.unit;
  const obs0 = (existing?.observations ?? {}) as { load?: string; readings?: CreepReading[] };
  const [load, setLoad] = useState(obs0.load ?? '');
  const [readings, setReadings] = useState<CreepReading[]>(
    obs0.readings?.length ? obs0.readings : [
      { t_min: '0', I: '', dL: '' },
      { t_min: '5', I: '', dL: '' },
      { t_min: '15', I: '', dL: '' },
      { t_min: '30', I: '', dL: '' },
    ],
  );
  const [busy, setBusy] = useState(false);

  const live = useMemo(() => {
    const L = pd(load);
    if (L === null) return null;
    let mpe: ReturnType<typeof mpeOf> | null = null;
    try { mpe = mpeOf(engineInst, L, mpeContext); } catch { return null; }
    const step = resolutionG ?? engineInst.ranges[0].d;
    const pts = readings
      .map((r) => ({ t: pd(r.t_min), P: pointError(pd(r.I) ?? 0 as never, 0 as never, pd(r.dL), step).P }))
      .filter(
        (p): p is { t: NonNullable<ReturnType<typeof pd>>; P: Decimal } =>
          p.t !== null && p.P !== null,
      )
      .sort((a, b) => a.t.comparedTo(b.t));
    if (pts.length === 0) return null;
    const P0 = pts[0].P;
    const rows = pts.map((p) => ({ t: p.t, dP: p.P.minus(P0) }));
    const aLim = engineInst.smallestE.times(0.5);
    const bLim = engineInst.smallestE.times(0.2);
    const within30 = rows.filter((r) => r.t.lte(30));
    const a1 = within30.length >= 2 && within30.every((r) => r.dP.abs().lte(aLim));
    const p15 = rows.find((r) => r.t.eq(15));
    const p30 = rows.find((r) => r.t.eq(30));
    const a2 = !!p15 && !!p30 && p30.dP.minus(p15.dP).abs().lte(bLim);
    if (a1 && a2) return { rows, aLim, mode: 'a) 30-min — PASS', pass: true };
    const has4h = pts[pts.length - 1].t.gte(240);
    if (has4h) {
      const b = rows.every((r) => r.dP.abs().lte(mpe!));
      return { rows, aLim, mode: b ? 'b) 4-h — PASS' : 'b) 4-h — FAIL', pass: b };
    }
    return { rows, aLim, mode: 'a) not met — 4-h data pending', pass: null };
  }, [load, readings, engineInst, resolutionG, mpeContext]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <label className="text-xs text-slate-600">
          Load ({unit})
          <input value={load} disabled={readOnly} inputMode="decimal" onChange={(e) => setLoad(e.target.value)}
            className="mt-1 block w-32 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" />
        </label>
        <span className="text-sm">{live?.mode ?? '—'}</span>
        <span className="ml-auto"><PassFailBadge pass={live?.pass ?? null} /></span>
      </div>
      <table className="w-full max-w-xl text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
          <tr><th className="px-2 py-1 text-left">t (min)</th><th className="px-2 py-1 text-left">I</th><th className="px-2 py-1 text-left">ΔL</th><th className="px-2 py-1 text-left">ΔP</th></tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {readings.map((r, i) => (
            <tr key={i}>
              <td className="px-2 py-1"><input value={r.t_min} disabled={readOnly} inputMode="decimal"
                onChange={(e) => setReadings(readings.map((x, j) => (j === i ? { ...x, t_min: e.target.value } : x)))}
                className="w-20 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" /></td>
              <td className="px-2 py-1"><input value={r.I} disabled={readOnly} inputMode="decimal"
                onChange={(e) => setReadings(readings.map((x, j) => (j === i ? { ...x, I: e.target.value } : x)))}
                className="w-28 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" /></td>
              <td className="px-2 py-1"><input value={r.dL} disabled={readOnly} inputMode="decimal"
                onChange={(e) => setReadings(readings.map((x, j) => (j === i ? { ...x, dL: e.target.value } : x)))}
                className="w-24 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" /></td>
              <td className="px-2 py-1 text-right font-mono text-slate-600">
                {live?.rows?.[i] ? `${fmtU(live.rows[i].dP, unit)} (limit ${fmtU(live.aLim, unit)})` : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!readOnly && (
        <div className="flex gap-3">
          <Button loading={busy} onClick={async () => { setBusy(true); try { await onSubmit({ load, readings }); } finally { setBusy(false); } }}>
            Save creep test
          </Button>
          <Button variant="secondary" onClick={() => setReadings([...readings, { t_min: '', I: '', dL: '' }])}>+ Add reading</Button>
        </div>
      )}
    </div>
  );
}