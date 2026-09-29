import { useState } from 'react';
import { getRuleset, listRulesets } from '../api/admin';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';

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

  if (list.loading || (activeId && detail.loading)) return <Spinner />;
  if (list.error) return <p className="text-sm text-red-600">{list.error}</p>;

  const doc = (detail.data?.document ?? {}) as RulesetDocument;
  const bands = cleanKeys((doc.mpe_bands ?? {}) as Record<string, unknown>);
  const t3 = cleanKeys((doc.classification_table3 ?? {}) as Record<string, unknown>);
  const constants = Object.entries(doc.constants ?? {})
    .filter(([k]) => !k.startsWith('_'));

  return (
    <div className="space-y-6">
      <Card title="OIML rule sets — rules are versioned DATA, not code">
        <div className="flex flex-wrap gap-2">
          {(list.data ?? []).map((r) => (
            <button key={r.id} onClick={() => setSelected(r.id)}
              className={`rounded-lg px-4 py-2 text-left text-sm ring-1 ring-inset transition ${
                activeId === r.id
                  ? 'bg-primary-600 text-white ring-primary-600'
                  : 'bg-white text-slate-700 ring-slate-300 hover:bg-slate-50'
              }`}>
              <span className="block font-semibold">{r.id}</span>
              <span className="block text-[11px] opacity-80">
                sha256 {r.sha256.slice(0, 12)}…
              </span>
            </button>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-500">
          When OIML publishes a revision, a new JSON rule set is added — every constant
          carries its clause number, and every report stores the exact rule-set hash it
          was evaluated against. No code changes, full reproducibility.
        </p>
      </Card>

      {detail.data && (
        <>
          <Card title={`MPE bands — Table 6 (initial verification) · ${detail.data.id}`}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                    <th className="py-2 pr-4">Class</th>
                    <th className="py-2 pr-4">|MPE|</th>
                    <th className="py-2">Load range (in e)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {Object.entries(bands).flatMap(([cls, arr]) =>
                    (arr as Band[]).map((b, i) => (
                      <tr key={`${cls}-${i}`}>
                        <td className="py-2 pr-4 font-semibold">{cls}</td>
                        <td className="py-2 pr-4 font-mono">± {b.mult} e</td>
                        <td className="py-2 font-mono text-xs">
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
            <p className="mt-2 text-xs text-slate-500">In service: MPE × 2 (clause 3.5.2).</p>
          </Card>

          <Card title="Classification — Table 3 (e bands, n limits, Min)">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                    <th className="py-2 pr-4">Class</th>
                    <th className="py-2 pr-4">e range (g)</th>
                    <th className="py-2 pr-4">n min</th>
                    <th className="py-2 pr-4">n max</th>
                    <th className="py-2">Min</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {CLASSES.flatMap((cls) =>
                    t3Rows(t3[cls]).map((row, i) => (
                      <tr key={`${cls}-${i}`}>
                        <td className="py-2 pr-4 font-semibold">{cls}</td>
                        <td className="py-2 pr-4 font-mono text-xs">
                          {row.e_min_g} … {row.e_max_g ?? '∞'}
                        </td>
                        <td className="py-2 pr-4 font-mono">{row.n_min}</td>
                        <td className="py-2 pr-4 font-mono">{row.n_max ?? '∞'}</td>
                        <td className="py-2 font-mono text-xs">{row.min_in_e} × e</td>
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Test catalogue (R 76-2 forms) & applicability">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                    <th className="py-2 pr-4">Form</th>
                    <th className="py-2 pr-4">Kind</th>
                    <th className="py-2 pr-4">Clause</th>
                    <th className="py-2">Required</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(doc.test_catalogue?.entries ?? []).map((e) => (
                    <tr key={e.kind}>
                      <td className="py-2 pr-4 font-mono text-xs">{e.form_no}</td>
                      <td className="py-2 pr-4 font-medium">{e.kind}</td>
                      <td className="py-2 pr-4 font-mono text-xs text-slate-500">{e.clause}</td>
                      <td className="py-2">
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

          <Card title="Constants (every value carries its clause)">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                    <th className="py-2 pr-4">Key</th>
                    <th className="py-2 pr-4">Value</th>
                    <th className="py-2">Clause</th>
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
                      <tr key={key}>
                        <td className="py-2 pr-4 font-mono text-xs">{key}</td>
                        <td className="py-2 pr-4 font-mono text-xs">{JSON.stringify(rest)}</td>
                        <td className="py-2 font-mono text-xs text-slate-500">{clause}</td>
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