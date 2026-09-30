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
  const [exportError, setExportError] = useState<string | null>(null);

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
    setExportError(null);
    try {
      const info = await exportReport(id, format);
      await downloadAuthed(
        `/api${info.download_url.replace('/api', '')}`,
        `${reportNo.replace('/', '-')}_${format.toLowerCase()}_v${info.version}.${format.toLowerCase()}`,
      );
    } catch (err) {
      setExportError(apiErrorDetail(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-5">
      <header>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-700">Controlled records</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Report repository</h1>
        <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">Search, review, and export controlled type evaluation reports.</p>
      </header>

      <Card>
        <div className="mb-5 border-b border-slate-100 pb-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="w-full max-w-sm">
              <Input
                label="Report or instrument"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="LM/NAWI/2026/0001 or PS-15K"
              />
            </div>
            <p className="text-xs tabular-nums text-slate-500" aria-live="polite">
              {evaluations.loading ? 'Loading repository…' : `${rows.length} ${rows.length === 1 ? 'report' : 'reports'} in view`}
            </p>
          </div>
          <div className="mt-4 flex flex-wrap gap-2" aria-label="Filter reports by status">
            {FILTERS.map((s) => (
              <button
                key={s}
                type="button"
                aria-pressed={status === s}
                onClick={() => setStatus(s)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2 ${
                  status === s
                    ? 'bg-slate-900 text-white ring-slate-900'
                    : 'bg-white text-slate-600 ring-slate-300 hover:bg-slate-50'
                }`}
              >
                {s === 'ALL' ? 'All' : s.replaceAll('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {exportError && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <p className="font-semibold">The report could not be exported</p>
            <p className="mt-1 text-xs">{exportError}</p>
          </div>
        )}
        {(evaluations.error || instruments.error) && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <p className="font-semibold">Repository data could not be loaded</p>
            <p className="mt-1 text-xs">{evaluations.error || instruments.error}</p>
            <div className="mt-3 flex gap-2">
              {evaluations.error && <Button variant="secondary" onClick={evaluations.reload}>Retry reports</Button>}
              {instruments.error && <Button variant="secondary" onClick={instruments.reload}>Retry instruments</Button>}
            </div>
          </div>
        )}
        {evaluations.loading && (
          <div className="space-y-2" aria-label="Loading report repository">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-12 animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ))}
          </div>
        )}

        {!evaluations.loading && !evaluations.error && rows.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <p className="text-sm font-semibold text-slate-800">No reports match this view</p>
            <p className="mt-1 text-xs text-slate-500">Clear the search or choose another report status.</p>
          </div>
        )}

        {!evaluations.loading && !evaluations.error && rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[940px] text-left text-sm">
              <caption className="sr-only">Type evaluation report repository</caption>
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                  <th scope="col" className="px-3 py-2.5 font-semibold">Report no.</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Instrument</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Status</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Outcome</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Created</th>
                  <th scope="col" className="px-3 py-2.5 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((e) => {
                  const inst = instMap.get(e.instrument_id);
                  return (
                    <tr key={e.id} className="transition-colors hover:bg-slate-50">
                      <td className="px-3 py-3 font-mono text-xs font-semibold tabular-nums text-teal-800">
                        {e.report_no}
                      </td>
                      <td className="px-3 py-3 text-slate-700">
                        {inst ? `${inst.type_designation} · Class ${inst.accuracy_class}` : instruments.loading ? 'Loading…' : '—'}
                      </td>
                      <td className="px-3 py-3"><StatusBadge status={e.status} /></td>
                      <td className="px-3 py-3">
                        {e.outcome ? <OutcomeBadge outcome={e.outcome} /> : <span className="text-slate-400">—</span>}
                      </td>
                      <td className="whitespace-nowrap px-3 py-3 text-xs tabular-nums text-slate-500">{fmtDateTime(e.created_at)}</td>
                      <td className="px-3 py-3 text-right">
                        <div className="flex justify-end gap-1.5">
                          <Button variant="secondary" className="!px-2.5 !py-1.5"
                            onClick={() => openPrintableHtml(printPath(e.id))}>
                            Preview
                          </Button>
                          <Button variant="secondary" className="!px-2.5 !py-1.5"
                            loading={busy === `${e.id}:PDF`}
                            onClick={() => doExport(e.id, 'PDF', e.report_no)}>
                            PDF
                          </Button>
                          <Button variant="secondary" className="!px-2.5 !py-1.5"
                            loading={busy === `${e.id}:DOCX`}
                            onClick={() => doExport(e.id, 'DOCX', e.report_no)}>
                            Word
                          </Button>
                          <Link to={`/evaluations/${e.id}`}
                            className="self-center rounded px-2 py-1 text-sm font-semibold text-teal-800 hover:bg-teal-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2">
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
    </div>
  );
}
