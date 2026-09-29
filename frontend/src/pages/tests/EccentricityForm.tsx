import { useMemo, useState } from 'react';
import Decimal from 'decimal.js';
import { fmtU, mpeOf, passes, pd, zeroErrorG } from '../../lib/calc';
import { Button } from '../../components/ui/Button';
import { PassFailBadge } from '../../components/data-display/PassFailBadge';
import type { TestFormProps } from './types';

interface EccObs {
  test_load: string;
  zero: { L: string; I: string; dL: string };
  locations: { location: number; I: string; dL: string }[];
}

export default function EccentricityForm({
  instrument, engineInst, resolutionG, mpeContext, existing, readOnly, onSubmit,
}: TestFormProps) {
  const unit = instrument.unit;
  const obs0 = (existing?.observations ?? {}) as Partial<EccObs>;
  const [testLoad, setTestLoad] = useState(obs0.test_load ?? '');
  const [zero, setZero] = useState(obs0.zero ?? { L: '0', I: '', dL: '' });
  const [locations, setLocations] = useState(
    obs0.locations?.length
      ? obs0.locations
      : Array.from({ length: 5 }, (_, i) => ({ location: i + 1, I: '', dL: '' })),
  );
  const [busy, setBusy] = useState(false);

  const live = useMemo(() => {
    const L = pd(testLoad);
    if (L === null) return null;
    let mpe = null;
    try {
      mpe = mpeOfLive(L);
    } catch {
      return null;
    }
    const step = resolutionG ?? engineInst.rangeForLoad(L).d;
    const e0 = zeroErrorG(zero, step) ?? new (zeroCtor())(0);
    return locations.map((loc) => {
      const I = pd(loc.I);
      if (I === null) return { location: loc.location, Ec: null, pass: null };
      const dL = pd(loc.dL) ?? new (zeroCtor())(0);
      const Ec = I.plus(step.div(2)).minus(dL).minus(L).minus(e0);
      return { location: loc.location, Ec, pass: passes(Ec, mpe!) };
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [testLoad, zero, locations, engineInst, resolutionG, mpeContext]);

  function mpeOfLive(L: ReturnType<typeof pd>) {
    return mpeOf(engineInst, L!, mpeContext);
  }
  function zeroCtor() {
    return Decimal;
  }

  const expected = engineInst.max.plus(engineInst.tarePlus).div(3);

  async function save() {
    setBusy(true);
    const cleaned = locations.filter((l) => l.I.trim() !== '');
    try {
      await onSubmit({ test_load: testLoad, zero, locations: cleaned });
    } finally {
      setBusy(false);
    }
  }

  const anyResult = live?.some((r) => r.pass !== null) ?? false;
  const allPass = live?.every((r) => r.pass !== false) ?? false;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4 rounded-lg bg-slate-50 px-4 py-3 text-sm ring-1 ring-inset ring-slate-200">
        <span>Default test load ⅓(Max+T₊) = <b className="font-mono">{fmtU(expected, unit)} {unit}</b> (3.6.2.1)</span>
        <span className="ml-auto flex items-center gap-2">
          Live: <PassFailBadge pass={anyResult ? allPass : null} />
        </span>
      </div>

      <div className="flex items-end gap-4">
        <label className="text-xs text-slate-600">
          Test load ({unit}) *
          <input value={testLoad} disabled={readOnly} inputMode="decimal"
            onChange={(e) => setTestLoad(e.target.value)}
            className="mt-1 block w-36 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" />
        </label>
        {(['L', 'I', 'dL'] as const).map((f) => (
          <label key={f} className="text-xs text-slate-600">
            zero {f}
            <input value={zero[f]} disabled={readOnly} inputMode="decimal"
              onChange={(e) => setZero({ ...zero, [f]: e.target.value })}
              className="mt-1 block w-24 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" />
          </label>
        ))}
      </div>

      <table className="w-full max-w-2xl text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
          <tr>
            <th className="px-2 py-2 text-left">Position</th>
            <th className="px-2 py-2 text-left">I ({unit})</th>
            <th className="px-2 py-2 text-left">ΔL</th>
            <th className="px-2 py-2 text-left">Ec</th>
            <th className="px-2 py-2">Result</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {locations.map((loc, i) => {
            const r = live?.[i];
            return (
              <tr key={loc.location}>
                <td className="px-2 py-1 font-medium">{loc.location}</td>
                <td className="px-2 py-1">
                  <input value={loc.I} disabled={readOnly} inputMode="decimal"
                    onChange={(e) => setLocations(locations.map((x, j) => (j === i ? { ...x, I: e.target.value } : x)))}
                    className="w-28 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" />
                </td>
                <td className="px-2 py-1">
                  <input value={loc.dL} disabled={readOnly} inputMode="decimal"
                    onChange={(e) => setLocations(locations.map((x, j) => (j === i ? { ...x, dL: e.target.value } : x)))}
                    className="w-24 rounded border border-slate-300 px-2 py-1 text-right font-mono text-sm disabled:bg-slate-100" />
                </td>
                <td className={`px-2 py-1 text-right font-mono ${r?.pass === false ? 'bg-red-50 font-semibold text-red-700' : r?.pass ? 'text-emerald-700' : 'text-slate-400'}`}>
                  {r?.Ec ? fmtU(r.Ec, unit) : '—'}
                </td>
                <td className="px-2 py-1 text-center"><PassFailBadge pass={r?.pass ?? null} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {!readOnly && (
        <Button onClick={save} loading={busy}>Save eccentricity test</Button>
      )}
    </div>
  );
}