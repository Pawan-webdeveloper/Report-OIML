import { Fragment, useMemo, useState } from 'react';
import {
  evaluateWeighingLive, fmtU, suggestLoadsG,
  type DirectionIn, type PointRowIn, type ZeroRowIn,
} from '../../lib/calc';
import { Button } from '../../components/ui/Button';
import { PassFailBadge } from '../../components/data-display/PassFailBadge';
import type { TestFormProps } from './types';

const emptyDir = (): DirectionIn => ({ I: '', dL: '' });
const emptyRow = (): PointRowIn => ({ L: '', up: emptyDir(), down: emptyDir() });

export default function WeighingForm({
  instrument, engineInst, resolutionG, mpeContext, existing, readOnly, onSubmit,
}: TestFormProps) {
  const [zero, setZero] = useState<ZeroRowIn>(
    (existing?.observations as { zero?: ZeroRowIn } | null)?.zero ?? { L: '0', I: '', dL: '' },
  );
  const [points, setPoints] = useState<PointRowIn[]>(
    (existing?.observations as { points?: PointRowIn[] } | null)?.points?.length
      ? (existing!.observations as { points: PointRowIn[] }).points
      : Array.from({ length: 5 }, emptyRow),
  );
  const [busy, setBusy] = useState(false);

  const unit = instrument.unit;
  const live = useMemo(
    () => evaluateWeighingLive({ zero, points }, engineInst, mpeContext, resolutionG),
    [zero, points, engineInst, mpeContext, resolutionG],
  );

  function suggest() {
    const loads = suggestLoadsG(engineInst, 10)
      .map((g) => g.toString());
    setPoints((prev) => {
      const next = [...prev];
      loads.forEach((L, i) => {
        if (i < next.length) next[i] = { ...next[i], L };
        else next[i] = { ...emptyRow(), L };
      });
      return next;
    });
  }



  /** CSV columns: L, I_up, dL_up[, I_down, dL_down] — header row auto-skipped. */
  function importCsv(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      const rows: PointRowIn[] = [];
      for (const raw of String(reader.result ?? '').split(/\r?\n/)) {
        const line = raw.trim();
        if (!line) continue;
        const cells = line.split(/[,;\t]/).map((c) => c.trim());
        if (!/^-?\d/.test(cells[0] ?? '')) continue;      // skip header / junk
        rows.push({
          L: cells[0] ?? '',
          up: { I: cells[1] ?? '', dL: cells[2] ?? '' },
          down: { I: cells[3] ?? '', dL: cells[4] ?? '' },
        });
      }
      if (rows.length) setPoints(rows);
    };
    reader.readAsText(file);
  }



  async function save() {
    setBusy(true);
    const cleaned = points.filter((p) => p.L.trim() !== '');
    try {
      await onSubmit({ zero, points: cleaned });
    } finally {
      setBusy(false);
    }
  }

  const overall = live.anyObs ? (live.anyFail ? false : live.allPass) : null;

  return (
    <div className="space-y-5">
      {/* Live summary strip */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-l-4 border-slate-700 bg-slate-50 px-4 py-3 text-sm">
        <span>E₀ = <b className="font-mono">{fmtU(live.e0, unit)} {unit}</b></span>
        <span>step = <b className="font-mono">{fmtU(resolutionG ?? engineInst.ranges[0].d, unit)} {unit}</b></span>
        <span>e = <b className="font-mono">{fmtU(engineInst.smallestE, unit)} {unit}</b></span>
        <span className="ml-auto flex items-center gap-2">
          Live verdict: <PassFailBadge pass={overall} />
        </span>
      </div>

      <div className="overflow-x-auto border border-slate-300">
        <table className="min-w-[62rem] w-full text-sm">
          <thead className="bg-slate-100 text-xs font-semibold uppercase tracking-wide text-slate-600">
            <tr>
              <th className="px-2 py-2 text-left">Load L ({unit})</th>
              <th className="px-2 py-2 text-left">↑ I</th>
              <th className="px-2 py-2 text-left">↑ ΔL</th>
              <th className="px-2 py-2 text-left">↑ Ec</th>
              <th className="px-2 py-2 text-left">↓ I</th>
              <th className="px-2 py-2 text-left">↓ ΔL</th>
              <th className="px-2 py-2 text-left">↓ Ec</th>
              <th className="px-2 py-2 text-left">MPE</th>
              <th className="px-2 py-2">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {points.map((p, i) => {
              const row = live.rows[i];
              const cellColor = (c: { pass: boolean } | null) =>
                c ? (c.pass ? 'text-emerald-700' : 'bg-red-50 text-red-700 font-semibold') : 'text-slate-400';
              return (
                <tr key={i} className="hover:bg-slate-50/70">
                  <td className="px-2 py-1">
                    <input value={p.L} disabled={readOnly} inputMode="decimal"
                      onChange={(e) => setPoints(points.map((x, j) => (j === i ? { ...x, L: e.target.value } : x)))}
                      className="min-h-11 w-24 rounded-md border border-slate-300 px-2 text-right font-mono text-sm tabular-nums outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100" />
                  </td>
                  {(['up', 'down'] as const).map((dirn) => (
                    <Fragment key={dirn}>
                      <td className="px-2 py-1">
                        <input value={p[dirn].I} disabled={readOnly} inputMode="decimal"
                          onChange={(e) => setPoints(points.map((x, j) => (j === i ? { ...x, [dirn]: { ...x[dirn], I: e.target.value } } : x)))}
                           className="min-h-11 w-24 rounded-md border border-slate-300 px-2 text-right font-mono text-sm tabular-nums outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100" />
                      </td>
                      <td className="px-2 py-1">
                        <input value={p[dirn].dL} disabled={readOnly} inputMode="decimal"
                          onChange={(e) => setPoints(points.map((x, j) => (j === i ? { ...x, [dirn]: { ...x[dirn], dL: e.target.value } } : x)))}
                           className="min-h-11 w-20 rounded-md border border-slate-300 px-2 text-right font-mono text-sm tabular-nums outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100" />
                      </td>
                      <td className={`px-2 py-1 text-right font-mono ${cellColor(row?.[dirn] ?? null)}`}>
                        {row?.[dirn] ? fmtU(row[dirn]!.Ec, unit) : '—'}
                      </td>
                    </Fragment>
                  ))}
                  <td className="px-2 py-1 text-right font-mono text-slate-500">
                    {row?.mpe ? fmtU(row.mpe, unit) : '—'}
                  </td>
                  <td className="px-2 py-1">
                    {row && (row.up || row.down) ? (
                      <PassFailBadge pass={row.up || row.down ? !(row.up?.pass === false || row.down?.pass === false) && (row.up?.pass ?? true) && (row.down?.pass ?? true) : null} />
                    ) : (
                      <PassFailBadge pass={null} />
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Zero row */}
      <div className="border border-slate-200 p-4">
        <p className="mb-2 text-sm font-semibold text-slate-700">
          Zero row <span className="font-normal text-slate-500">(near-zero *; with auto-zero in operation use L = 10 e)</span>
        </p>
        <div className="flex flex-wrap items-end gap-3">
          {(['L', 'I', 'dL'] as const).map((f) => (
            <label key={f} className="text-xs text-slate-600">
              {f} ({unit})
              <input value={zero[f]} disabled={readOnly} inputMode="decimal"
                onChange={(e) => setZero({ ...zero, [f]: e.target.value })}
                 className="mt-1 block min-h-11 w-28 rounded-md border border-slate-300 px-2 text-right font-mono text-sm tabular-nums outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100" />
            </label>
          ))}
          <span className="text-sm text-slate-500">
            E₀ = <b className="font-mono">{fmtU(live.e0, unit)} {unit}</b>
          </span>
        </div>
      </div>

      {!readOnly && (
        <div className="sticky bottom-0 z-10 -mx-5 flex flex-wrap gap-2 border-t border-slate-300 bg-white/95 px-5 py-3 backdrop-blur">
          <Button className="min-h-12" onClick={save} loading={busy}>Save weighing test</Button>
          <Button className="min-h-12" variant="secondary" onClick={suggest}>Suggest MPE change-point loads</Button>
          <label className="inline-flex min-h-12 cursor-pointer items-center justify-center rounded-lg bg-white px-4 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-inset ring-slate-300 hover:bg-slate-50 focus-within:ring-2 focus-within:ring-primary-500 focus-within:ring-offset-2">
            Import CSV
            <input type="file" accept=".csv,text/csv" className="sr-only"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) importCsv(f);
                e.target.value = '';
              }} />
          </label>
          <Button className="min-h-12" variant="secondary" onClick={() => setPoints([...points, emptyRow()])}>Add row</Button>
        </div>
      )}
    </div>
  );
}
