import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  approveEvaluation, archiveEvaluation, getEvaluation, getRequiredTests,
  linkEquipment, listAllEquipment, listEvaluationEquipment, reopenEvaluation,
  returnEvaluation, startReview, submitEvaluation,
} from '../api/evaluations';
import { getInstrument } from '../api/instruments';
import { listTestRecords } from '../api/tests';
import { apiErrorDetail } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { useAuthStore } from '../store/authStore';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';
import { OutcomeBadge } from '../components/ui/Badge';
import { VerdictBadge } from '../components/data-display/PassFailBadge';
import StatusStepper from '../components/data-display/StatusStepper';
import { testFormNo, testTitle } from '../lib/testmeta';
import { fmtDateTime } from '../lib/format';
import { exportReport, exportDownloadPath, listExports, printPath } from '../api/reports';
import { downloadAuthed, openPrintableHtml } from '../lib/download';

const EDITABLE = ['DRAFT', 'IN_PROGRESS', 'RETURNED'];

export default function EvaluationDetailPage() {
  const { id = '' } = useParams();
  const user = useAuthStore((s) => s.user);
  const role = user?.role;

  const evaluation = useAsync(() => getEvaluation(id), [id]);
  const instId = evaluation.data?.instrument_id ?? null;
  const instrument = useAsync(
    async () => (instId ? getInstrument(instId) : null),
    [instId],
  );
  const preview = useAsync(() => getRequiredTests(id), [id]);
  const records = useAsync(() => listTestRecords(id), [id]);
  const linkedEq = useAsync(() => listEvaluationEquipment(id), [id]);
  const allEq = useAsync(() => listAllEquipment(), [id]);
  const reportExports = useAsync(() => listExports(id), [id]);
  const [reportBusy, setReportBusy] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const [actionError, setActionError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [showReturn, setShowReturn] = useState(false);
  const [returnComment, setReturnComment] = useState('');

  const ev = evaluation.data;
  const inst = instrument.data;
  const editable = !!ev && EDITABLE.includes(ev.status);

  async function doExport(fmt: 'PDF' | 'DOCX') {
    setReportBusy(fmt);
    setReportError(null);
    try {
      const info = await exportReport(id, fmt);
      await downloadAuthed(
        exportDownloadPath(id, info.id),
        `${ev?.report_no.replaceAll('/', '-') ?? 'report'}_${fmt.toLowerCase()}_v${info.version}.${fmt.toLowerCase()}`,
      );
      reportExports.reload();
    } catch (err) {
      setReportError(apiErrorDetail(err));
    } finally {
      setReportBusy(null);
    }
  }

  async function run(name: string, fn: () => Promise<unknown>) {
    setBusyAction(name);
    setActionError(null);
    try {
      await fn();
      evaluation.reload();
      preview.reload();
      records.reload();
      linkedEq.reload();
    } catch (err) {
      setActionError(apiErrorDetail(err));
    } finally {
      setBusyAction(null);
    }
  }

  if (evaluation.loading) return <Spinner />;
  if (evaluation.error || !ev)
    return <p className="text-sm text-red-600">{evaluation.error ?? 'Not found'}</p>;

  const linkedIds = new Set((linkedEq.data ?? []).map((e) => e.id));
  const recordFor = (kind: string) =>
    (records.data ?? []).find((r) => r.kind === kind && r.instance_no === 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-sm font-semibold text-primary-700">{ev.report_no}</p>
            <p className="mt-1 text-sm text-slate-500">
              {inst ? `${inst.type_designation} · Class ${inst.accuracy_class}` : '…'} ·{' '}
              {ev.purpose.replaceAll('_', ' ')} · MPE {ev.mpe_context === 'IN_SERVICE' ? 'in service (2×)' : 'initial'}
            </p>
            <p className="mt-0.5 text-xs text-slate-400">Created {fmtDateTime(ev.created_at)}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            {ev.outcome && <OutcomeBadge outcome={ev.outcome} />}
            {ev.approval_hash && (
              <p className="font-mono text-[10px] text-slate-400" title={ev.approval_hash}>
                approval-hash: {ev.approval_hash.slice(0, 16)}…
              </p>
            )}
          </div>
        </div>
        <div className="mt-4 border-t border-slate-100 pt-4">
          <StatusStepper status={ev.status} />
        </div>
      </Card>

      {actionError && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-inset ring-red-200">
          {actionError}
        </div>
      )}

      {/* Workflow actions */}
      <Card title="Workflow">
        <div className="flex flex-wrap items-center gap-3">
          {role === 'ENGINEER' && ev.status === 'IN_PROGRESS' && (
            <Button loading={busyAction === 'submit'} onClick={() => run('submit', () => submitEvaluation(id))}>
              Submit for review
            </Button>
          )}
          {role === 'ENGINEER' && ev.status === 'RETURNED' && (
            <Button loading={busyAction === 'reopen'} onClick={() => run('reopen', () => reopenEvaluation(id))}>
              Reopen (fix & rework)
            </Button>
          )}
          {role === 'REVIEWER' && ev.status === 'SUBMITTED' && (
            <Button loading={busyAction === 'review'} onClick={() => run('review', () => startReview(id))}>
              Start review
            </Button>
          )}
          {role === 'REVIEWER' && ev.status === 'UNDER_REVIEW' && (
            <>
              <Button loading={busyAction === 'approve'} onClick={() => run('approve', () => approveEvaluation(id))}>
                ✓ Approve
              </Button>
              <Button variant="secondary" onClick={() => setShowReturn(!showReturn)}>
                ↩ Return with comments
              </Button>
            </>
          )}
          {role === 'ADMIN' && ev.status === 'APPROVED' && (
            <Button variant="secondary" loading={busyAction === 'archive'} onClick={() => run('archive', () => archiveEvaluation(id))}>
              Archive
            </Button>
          )}
          {!editable && ev.status !== 'APPROVED' && ev.status !== 'ARCHIVED' && (
            <p className="text-xs text-slate-500">
              {ev.status === 'DRAFT' && 'Save any test page to move this evaluation to In Progress.'}
              {ev.status === 'SUBMITTED' && 'Waiting for a reviewer.'}
              {ev.status === 'UNDER_REVIEW' && 'Under review — approve or return.'}
            </p>
          )}
        </div>
        {showReturn && role === 'REVIEWER' && (
          <div className="mt-4 flex max-w-xl gap-2">
            <input
              value={returnComment}
              onChange={(e) => setReturnComment(e.target.value)}
              placeholder="What must the engineer fix?"
              className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300"
            />
            <Button
              variant="danger"
              loading={busyAction === 'return'}
              disabled={!returnComment.trim()}
              onClick={() => run('return', () => returnEvaluation(id, returnComment)).then(() => setShowReturn(false))}
            >
              Return
            </Button>
          </div>
        )}
      </Card>

            {/* Report exports */}
      <Card title="Type Evaluation Report (R 76-2)">
        {reportError && (
          <div className="mb-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-inset ring-amber-200">
            {reportError}
          </div>
        )}
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => openPrintableHtml(printPath(id))}>
            👁 Preview (print-ready)
          </Button>
          <Button loading={reportBusy === 'PDF'} onClick={() => doExport('PDF')}>
            ⬇ PDF
          </Button>
          <Button loading={reportBusy === 'DOCX'} onClick={() => doExport('DOCX')}>
            ⬇ Word (editable)
          </Button>
        </div>
        {reportExports.data && reportExports.data.length > 0 && (
          <table className="mt-4 w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 uppercase text-slate-500">
                <th className="py-1 pr-3">Format</th>
                <th className="py-1 pr-3">Version</th>
                <th className="py-1 pr-3">SHA-256</th>
                <th className="py-1 pr-3">Generated</th>
                <th className="py-1" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {reportExports.data.map((x) => (
                <tr key={x.id}>
                  <td className="py-1 pr-3 font-medium">{x.format}</td>
                  <td className="py-1 pr-3">v{x.version}</td>
                  <td className="py-1 pr-3 font-mono">{x.sha256.slice(0, 16)}…</td>
                  <td className="py-1 pr-3 text-slate-500">{fmtDateTime(x.created_at)}</td>
                  <td className="py-1 text-right">
                    <button
                      className="font-medium text-primary-700 hover:underline"
                      onClick={() =>
                        downloadAuthed(exportDownloadPath(id, x.id),
                          `report_${x.format.toLowerCase()}_v${x.version}.${x.format.toLowerCase()}`)
                      }
                    >
                      Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="mt-3 text-xs text-slate-500">
          PDF uses the server PDF engine when installed; otherwise use Preview →
          “Print / Save as PDF”. Word exports are always generated.
        </p>
      </Card>

      {/* Required tests checklist */}
      <Card title={`Required tests (${preview.data?.outcome ?? '…'})`}>
        {preview.data ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                  <th className="py-2 pr-4">Form</th>
                  <th className="py-2 pr-4">Test</th>
                  <th className="py-2 pr-4">Verdict</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {preview.data.required.map((kind) => {
                  const rec = recordFor(kind);
                  const canEdit = editable && role === 'ENGINEER';
                  return (
                    <tr key={kind} className="hover:bg-slate-50">
                      <td className="py-2 pr-4 font-mono text-xs text-slate-500">{testFormNo(kind)}</td>
                      <td className="py-2 pr-4 font-medium">{testTitle(kind)}</td>
                      <td className="py-2 pr-4"><VerdictBadge verdict={rec?.verdict ?? 'PENDING'} /></td>
                      <td className="py-2 text-right">
                        <Link
                          to={`/evaluations/${id}/tests/${kind}/1`}
                          className="text-sm font-medium text-primary-700 hover:underline"
                        >
                          {rec ? 'View / edit' : canEdit ? 'Enter data' : 'Open'}
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <Spinner />
        )}
      </Card>

      {/* Test equipment (submission gate requires ≥1 link) */}
      <Card title="Test equipment (traceability — R 76-2 p.8)">
        {allEq.data && (
          <ul className="divide-y divide-slate-100">
            {allEq.data.map((eq) => {
              const linked = linkedIds.has(eq.id);
              return (
                <li key={eq.id} className="flex items-center justify-between py-2 text-sm">
                  <div>
                    <p className="font-medium">{eq.name ?? eq.kind}</p>
                    <p className="text-xs text-slate-500">
                      {eq.kind} · {eq.serial_no ?? '—'} · {eq.accuracy_class_or_uncertainty ?? '—'}
                    </p>
                  </div>
                  {linked ? (
                    <Badge label="Linked" className="bg-emerald-100 text-emerald-800 ring-emerald-300" />
                  ) : (
                    editable &&
                    (role === 'ENGINEER' || role === 'ADMIN') && (
                      <Button variant="secondary" onClick={() => run('link', () => linkEquipment(id, eq.id))}>
                        Link
                      </Button>
                    )
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      {/* Other recorded pages */}
      {records.data && records.data.length > 0 && (
        <Card title="All recorded pages">
          <div className="flex flex-wrap gap-2">
            {records.data.map((r) => (
              <Link
                key={r.id}
                to={`/evaluations/${id}/tests/${r.kind}/${r.instance_no}`}
                className="rounded-lg border border-slate-200 px-3 py-2 text-xs hover:bg-slate-50"
              >
                <span className="font-mono text-slate-400">#{r.form_no ?? '?'}</span>{' '}
                <span className="font-medium">{testTitle(r.kind)}</span>{' '}
                <VerdictBadge verdict={r.verdict} />
              </Link>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}