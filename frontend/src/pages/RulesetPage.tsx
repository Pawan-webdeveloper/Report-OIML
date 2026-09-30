import { useState } from 'react';
import { getRuleset, listRulesets } from '../api/admin';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

interface Band { up_to: string | null; mult: string }
interface T3Row {
  e_min_g: string; e_max_g: string | null;
  n_min: string; n_max: string | null; min_in_e: string;
}
interface CatalogueEntry {
  kind: string; form_no: string; clause: string; required?: boolean;
}
interface RulesetDocument {
  title?: string;
  mpe_bands?: Record<string, Band[]>;
  classification_table3?: Record<string, unknown>;
  constants?: Record<string, Record<string, unknown>>;
  test_catalogue?: { entries?: CatalogueEntry[] };
}

const CLASSES = ['I', 'II', 'III', 'IIII'];

function t3Rows(raw: unknown): T3Row[] {
  if (Array.isArray(raw)) return raw as T3Row[];
  if (raw && typeof raw === 'object') return [raw as T3Row];
  return [];
}

function cleanKeys(doc: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(doc).filter(([k]) => !k.startsWith('_')),
  );
}

export default function RulesetPage() {
  const list = useAsync(listRulesets);
  const [selected, setSelected] = useState<string | null>(null);
  const activeId = selected ?? list.data?.[0]?.id ?? null;
  const detail = useAsync(
    async () => (activeId ? getRuleset(activeId) : null),
    [activeId],
  );

  const doc = (detail.data?.document ?? {}) as RulesetDocument;
  const bands = cleanKeys((doc.mpe_bands ?? {}) as Record<string, unknown>);
  const t3 = cleanKeys((doc.classification_table3 ?? {}) as Record<string, unknown>);
  const constants = Object.entries(doc.constants ?? {})
    .filter(([k]) => !k.startsWith('_'));

  return (
    <div className="space-y-5">
      <header>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-700">Controlled methodology</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">OIML rule sets</h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">Versioned constants, clauses, and test applicability used to produce reproducible evaluation decisions.</p>
      </header>

      {list.loading && (
        <div className="space-y-3" aria-label="Loading rule sets">
          <div className="h-28 animate-pulse rounded-xl bg-slate-100 motion-reduce:animate-none" />
          <div className="h-64 animate-pulse rounded-xl bg-slate-100 motion-reduce:animate-none" />
        </div>
      )}

      {list.error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          <p className="font-semibold">Rule sets could not be loaded</p>
          <p className="mt-1 text-xs">{list.error}</p>
          <Button variant="secondary" className="mt-3" onClick={list.reload}>Retry</Button>
        </div>
      )}

      {!list.loading && !list.error && (list.data?.length ?? 0) === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-12 text-center">
          <p className="text-sm font-semibold text-slate-800">No rule sets available</p>
          <p className="mt-1 text-xs text-slate-500">Import a versioned rule set before running evaluations.</p>
        </div>
      )}

      {!list.loading && !list.error && (list.data?.length ?? 0) > 0 && (
      <Card title="Available versions">
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3" role="list" aria-label="Rule set versions">
          {(list.data ?? []).map((r) => (
            <button key={r.id} type="button" role="listitem" aria-pressed={activeId === r.id} onClick={() => setSelected(r.id)}
              className={`rounded-lg px-4 py-3 text-left text-sm ring-1 ring-inset transition focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2 ${
                activeId === r.id
                  ? 'bg-slate-900 text-white ring-slate-900'
                  : 'bg-white text-slate-700 ring-slate-300 hover:bg-slate-50'
              }`}>
              <span className="block font-semibold">{r.id}</span>
              <span className={`mt-1 block font-mono text-[11px] ${activeId === r.id ? 'text-slate-300' : 'text-slate-500'}`}>
                SHA-256 {r.sha256.slice(0, 12)}…
              </span>
            </button>
          ))}
        </div>
        <p className="mt-4 max-w-4xl text-xs leading-5 text-slate-500">
          Each revision is stored as a new data document. Every report retains the exact
          rule-set hash and clause references used during evaluation.
        </p>
      </Card>
      )}

      {activeId && detail.loading && (
        <div className="h-64 animate-pulse rounded-xl bg-slate-100 motion-reduce:animate-none" aria-label="Loading rule set detail" />
      )}

      {detail.error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          <p className="font-semibold">Rule-set detail could not be loaded</p>
          <p className="mt-1 text-xs">{detail.error}</p>
          <Button variant="secondary" className="mt-3" onClick={detail.reload}>Retry</Button>
        </div>
      )}

      {!detail.loading && !detail.error && detail.data && (
        <>
          <Card title={`MPE bands · Table 6 · ${detail.data.id}`}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-left text-sm">
                <caption className="sr-only">Maximum permissible error bands for initial verification</caption>
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                    <th scope="col" className="px-3 py-2.5 font-semibold">Class</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">|MPE|</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">Load range (in e)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {Object.entries(bands).flatMap(([cls, arr]) =>
                    (arr as Band[]).map((b, i) => (
                      <tr key={`${cls}-${i}`} className="transition-colors hover:bg-slate-50">
                        <td className="px-3 py-2.5 font-semibold text-slate-900">{cls}</td>
                        <td className="px-3 py-2.5 font-mono tabular-nums">± {b.mult} e</td>
                        <td className="px-3 py-2.5 font-mono text-xs tabular-nums text-slate-600">
                          {b.up_to === null
                            ? `m > ${String((arr as Band[])[i - 1]?.up_to ?? 0)}`
                            : `0 ≤ m ≤ ${b.up_to}`}
                        </td>
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-slate-500">In-service limit: MPE × 2, clause 3.5.2.</p>
          </Card>

          <Card title="Classification · Table 3">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <caption className="sr-only">Classification ranges, limits, and minimum capacity</caption>
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                    <th scope="col" className="px-3 py-2.5 font-semibold">Class</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">e range (g)</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">n minimum</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">n maximum</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">Minimum capacity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {CLASSES.flatMap((cls) =>
                    t3Rows(t3[cls]).map((row, i) => (
                      <tr key={`${cls}-${i}`} className="transition-colors hover:bg-slate-50">
                        <td className="px-3 py-2.5 font-semibold text-slate-900">{cls}</td>
                        <td className="px-3 py-2.5 font-mono text-xs tabular-nums text-slate-600">
                          {row.e_min_g} … {row.e_max_g ?? '∞'}
                        </td>
                        <td className="px-3 py-2.5 font-mono tabular-nums">{row.n_min}</td>
                        <td className="px-3 py-2.5 font-mono tabular-nums">{row.n_max ?? '∞'}</td>
                        <td className="px-3 py-2.5 font-mono text-xs tabular-nums">{row.min_in_e} × e</td>
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Test catalogue · R 76-2 forms">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[620px] text-left text-sm">
                <caption className="sr-only">Test catalogue forms and applicability</caption>
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                    <th scope="col" className="px-3 py-2.5 font-semibold">Form</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">Test</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">Clause</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">Applicability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(doc.test_catalogue?.entries ?? []).map((e) => (
                    <tr key={e.kind} className="transition-colors hover:bg-slate-50">
                      <td className="px-3 py-2.5 font-mono text-xs font-semibold text-slate-800">{e.form_no}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-900">{e.kind.replaceAll('_', ' ')}</td>
                      <td className="px-3 py-2.5 font-mono text-xs text-slate-500">{e.clause}</td>
                      <td className="px-3 py-2.5">
                        <Badge label={e.required ? 'Required' : 'If applicable'}
                          className={e.required
                            ? 'bg-emerald-100 text-emerald-800 ring-emerald-300'
                            : 'bg-slate-100 text-slate-600 ring-slate-300'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Referenced constants">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <caption className="sr-only">Rule-set constants and source clauses</caption>
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                    <th scope="col" className="px-3 py-2.5 font-semibold">Key</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">Value</th>
                    <th scope="col" className="px-3 py-2.5 font-semibold">Clause</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {constants.map(([key, val]) => {
                    const v = val as Record<string, unknown>;
                    const clause = typeof v.clause === 'string' ? v.clause : '—';
                    const rest = Object.fromEntries(
                      Object.entries(v).filter(
                        ([k]) => k !== 'clause' && !k.startsWith('_'),
                      ),
                    );
                    return (
                      <tr key={key} className="transition-colors hover:bg-slate-50">
                        <td className="px-3 py-2.5 font-mono text-xs font-semibold text-slate-800">{key}</td>
                        <td className="max-w-2xl px-3 py-2.5 font-mono text-xs leading-5 text-slate-700">{JSON.stringify(rest)}</td>
                        <td className="whitespace-nowrap px-3 py-2.5 font-mono text-xs text-slate-500">{clause}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
