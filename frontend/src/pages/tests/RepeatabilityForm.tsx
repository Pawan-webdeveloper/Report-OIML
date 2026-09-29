import { useMemo, useState } from 'react';
import type { Decimal } from 'decimal.js';
import { fmtU, mpeOf, pd, pointError } from '../../lib/calc';
import { Button } from '../../components/ui/Button';
import { PassFailBadge } from '../../components/data-display/PassFailBadge';
import type { TestFormProps } from './types';

interface Series {
  L: string;
  weighings: { I: string; dL: string }[];
}

export default function RepeatabilityForm({
  instrument, engineInst, resolutionG, mpeContext, existing, readOnly, onSubmit,
}: TestFormProps) {
  const unit = instrument.unit;
  const obs0 = (existing?.observations ?? {}) as { series?: Series[] };
  const [series, setSeries] = useState<Series[]>(
    obs0.series?.length ? obs0.series : [
      { L: '', weighings: Array.from({ length: 10 }, () => ({ I: '', dL: '' })) },
      { L: '', weighings: Array.from({ length: 10 }, () => ({ I: '', dL: '' })) },
    ],
  );
  const [busy, setBusy] = useState(false);

  const live = useMemo(() =>
    series.map((s) => {
      const L = pd(s.L);
      if (L === null) return null;
      let mpe: ReturnType<typeof mpeOf> | null = null;
      try { mpe = mpeOf(engineInst, L, mpeContext); } catch { return null; }
      const step = resolutionG ?? engineInst.rangeForLoad(L).d;
      const Ps: Decimal[] = [];
      const Es: Decimal[] = [];
      for (const w of s.weighings) {
        const I = pd(w.I);
        if (I === null) continue;
        const { P, E } = pointError(I, L, pd(w.dL), step);
        Ps.push(P); Es.push(E);
      }
      if (Ps.length === 0) return null;
      const spread = Ps.reduce((a, b) => (b.gt(a) ? b : a)).minus(Ps.reduce((a, b) => (b.lt(a) ? b : a)));
      const allWithin = Es.every((E) => E.abs().lte(mpe!));
      const spreadOk = spread.lte(mpe!);
      return { L, mpe, n: Ps.length, spread, allWithin, spreadOk, pass: allWithin && spreadOk };
    }), [series, engineInst, resolutionG, mpeContext]);

  async function save() {
    setBusy(true);
    const cleaned = series
      .map((s) => ({ L: s.L, weighings: s.weighings.filter((w) => w.I.trim() !== '') }))
      .filter((s) => s.L.trim() !== '');
    try {
      await onSubmit({ series: cleaned });
    } finally {
      setBusy(false);
    }
  }

  const anyResult = live.some((s) => s !== null);
  const allPass = live.every((s) => s === null || s.pass);

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 rounded-lg bg-slate-50 px-4 py-3 text-sm ring-1 ring-inset ring-slate-200">
        <span>Rule: every |E| ≤ MPE <b>and</b> Pmax − Pmin ≤ MPE (A.4.10)</span>
        <span className="ml-auto flex items-center gap-2">Live: <PassFailBadge pass={anyResult ? allPass : null} /></span>
      </div>

      {series.map((s, si) => {
        const r = live[si];
        return (
          <div key={si} className="rounded-lg border border-slate-200 p-4">
            <div className="mb-3 flex flex-wrap items-end gap-3">
              <label className="text-xs text-slate-600">
                Load {si + 1} ({unit})
                <input value={s.L} disabled={readOnly} inputMode="decimal"
                  onChange={(e) => setSeries(series.map((x, j) => (j === si ? { ...x, L: e.target.value } : x)))}
                  className="mt-1 block w-32 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" />
              </label>
              {r && (
                <span className="text-xs text-slate-600">
                  MPE <b className="font-mono">{fmtU(r.mpe, unit)}</b> · spread{' '}
                  <b className={`font-mono ${r.spreadOk ? 'text-emerald-700' : 'text-red-700'}`}>
                    {fmtU(r.spread, unit)}
                  </b>{' '}
                  · n={r.n}
                </span>
              )}
              <span className="ml-auto"><PassFailBadge pass={r?.pass ?? null} /></span>
              {!readOnly && series.length > 1 && (
                <button className="text-xs text-red-500 hover:underline"
                  onClick={() => setSeries(series.filter((_, j) => j !== si))}>remove series</button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
              {s.weighings.map((w, wi) => (
                <div key={wi} className="flex items-center gap-1">
                  <input value={w.I} disabled={readOnly} inputMode="decimal" placeholder="I"
                    onChange={(e) => setSeries(series.map((x, j) => j === si
                      ? { ...x, weighings: x.weighings.map((y, k) => (k === wi ? { ...y, I: e.target.value } : y)) }
                      : x))}
                    className="w-full rounded border border-slate-300 px-2 py-1 text-right font-mono text-xs disabled:bg-slate-100" />
                  <input value={w.dL} disabled={readOnly} inputMode="decimal" placeholder="ΔL"
                    onChange={(e) => setSeries(series.map((x, j) => j === si
                      ? { ...x, weighings: x.weighings.map((y, k) => (k === wi ? { ...y, dL: e.target.value } : y)) }
                      : x))}
                    className="w-full rounded border border-slate-300 px-2 py-1 text-right font-mono text-xs disabled:bg-slate-100" />
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {!readOnly && (
        <div className="flex gap-3">
          <Button onClick={save} loading={busy}>Save repeatability test</Button>
          <Button variant="secondary"
            onClick={() => setSeries([...series, { L: '', weighings: Array.from({ length: 10 }, () => ({ I: '', dL: '' })) }])}>
            + Add series
          </Button>
        </div>
      )}
    </div>
  );
}