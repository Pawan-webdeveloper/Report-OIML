import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { listEvaluations } from '../api/evaluations';
import { listInstruments } from '../api/instruments';
import { apiErrorDetail } from '../api/client';
import { exportReport, printPath } from '../api/reports';
import { downloadAuthed, openPrintableHtml } from '../lib/download';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { OutcomeBadge, StatusBadge } from '../components/ui/Badge';
import { fmtDateTime } from '../lib/format';
import type { EvalStatus } from '../types';

const FILTERS: (EvalStatus | 'ALL')[] = [
  'ALL', 'DRAFT', 'IN_PROGRESS', 'SUBMITTED', 'UNDER_REVIEW',
  'APPROVED', 'ARCHIVED',
];

export default function ReportsPage() {
  const evaluations = useAsync(listEvaluations);
  const instruments = useAsync(listInstruments);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState<EvalStatus | 'ALL'>('ALL');
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const instMap = useMemo(
    () => new Map((instruments.data ?? []).map((i) => [i.id, i])),
    [instruments.data],
  );

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (evaluations.data ?? []).filter((e) => {
      if (status !== 'ALL' && e.status !== status) return false;
      if (!needle) return true;
      const inst = instMap.get(e.instrument_id);
      return (
        e.report_no.toLowerCase().includes(needle) ||
        (inst?.type_designation.toLowerCase().includes(needle) ?? false)
      );
    });
  }, [evaluations.data, instMap, q, status]);

  async function doExport(id: string, format: 'PDF' | 'DOCX', reportNo: string) {
    setBusy(`${id}:${format}`);
    setError(null);
    try {
      const info = await exportReport(id, format);
      await downloadAuthed(
        `/api${info.download_url.replace('/api', '')}`,
        `${reportNo.replace('/', '-')}_${format.toLowerCase()}_v${info.version}.${format.toLowerCase()}`,
      );
    } catch (err) {
      setError(apiErrorDetail(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card title="Report repository — search & retrieval">
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="w-72">
          <Input
            label="Search (report no. or instrument)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="LM/NAWI/2026/0001 or PS-15K"
          />
        </div>
        <div className="flex flex-wrap gap-2 pb-1">
          {FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset ${
                status === s
                  ? 'bg-primary-600 text-white ring-primary-600'
                  : 'bg-white text-slate-600 ring-slate-300 hover:bg-slate-50'
              }`}
            >
              {s === 'ALL' ? 'All' : s.replaceAll('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-inset ring-red-200">
          {error}
        </div>
      )}
      {evaluations.loading && <p className="text-sm text-slate-500">Loading…</p>}

      {!evaluations.loading && rows.length === 0 && (
        <p className="py-10 text-center text-sm text-slate-500">No reports match.</p>
      )}

      {rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="py-2 pr-4">Report no.</th>
                <th className="py-2 pr-4">Instrument</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Outcome</th>
                <th className="py-2 pr-4">Created</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((e) => {
                const inst = instMap.get(e.instrument_id);
                return (
                  <tr key={e.id} className="hover:bg-slate-50">
                    <td className="py-3 pr-4 font-mono text-xs font-medium text-primary-700">
                      {e.report_no}
                    </td>
                    <td className="py-3 pr-4">
                      {inst ? `${inst.type_designation} · ${inst.accuracy_class}` : '—'}
                    </td>
                    <td className="py-3 pr-4"><StatusBadge status={e.status} /></td>
                    <td className="py-3 pr-4">
                      {e.outcome ? <OutcomeBadge outcome={e.outcome} /> : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="py-3 pr-4 text-slate-500">{fmtDateTime(e.created_at)}</td>
                    <td className="py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="secondary"
                          onClick={() => openPrintableHtml(printPath(e.id))}>
                          Preview
                        </Button>
                        <Button variant="secondary"
                          loading={busy === `${e.id}:PDF`}
                          onClick={() => doExport(e.id, 'PDF', e.report_no)}>
                          PDF
                        </Button>
                        <Button variant="secondary"
                          loading={busy === `${e.id}:DOCX`}
                          onClick={() => doExport(e.id, 'DOCX', e.report_no)}>
                          Word
                        </Button>
                        <Link to={`/evaluations/${e.id}`}
                          className="self-center text-sm font-medium text-primary-700 hover:underline">
                          Open
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}