import { useState } from 'react';
import { listAudit } from '../api/admin';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { fmtDateTime } from '../lib/format';

export default function AuditLogPage() {
  const [action, setAction] = useState('');
  const [entity, setEntity] = useState('');
  const { data, loading, error, reload } = useAsync(
    () => listAudit({ action: action || undefined, entity: entity || undefined, limit: 200 }),
    [action, entity],
  );

  return (
    <div className="space-y-5">
      <header>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-700">System assurance</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Audit trail</h1>
        <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">Immutable record of user and system activity. Results are limited to the latest 200 entries.</p>
      </header>

      <Card>
        <div className="mb-5 grid grid-cols-1 gap-3 border-b border-slate-100 pb-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
          <Input label="Action" value={action}
            onChange={(e) => setAction(e.target.value)}
            placeholder="EVALUATION, LOGIN, TEST_RECORD" />
          <Input label="Entity" value={entity}
            onChange={(e) => setEntity(e.target.value)}
            placeholder="evaluation, user, attachment" />
          <p className="self-end pb-2 text-xs tabular-nums text-slate-500" aria-live="polite">
            {loading ? 'Updating trail…' : `${data?.length ?? 0} entries returned`}
          </p>
        </div>

        {loading && (
          <div className="space-y-2" aria-label="Loading audit trail">
            {Array.from({ length: 7 }).map((_, index) => (
              <div key={index} className="h-11 animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ))}
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <p className="font-semibold">Audit trail could not be loaded</p>
            <p className="mt-1 text-xs">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={reload}>Retry</Button>
          </div>
        )}

        {!loading && !error && data && data.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <p className="text-sm font-semibold text-slate-800">No audit entries match</p>
            <p className="mt-1 text-xs text-slate-500">Adjust the action or entity filter to broaden the result.</p>
          </div>
        )}

        {!loading && !error && data && data.length > 0 && (
          <div className="max-h-[34rem] overflow-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
              <caption className="sr-only">Immutable system audit entries</caption>
              <thead className="sticky top-0 z-10">
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                  <th scope="col" className="px-3 py-2.5 font-semibold">Timestamp</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Action</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Entity</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Entity ID</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">User ID</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">IP address</th>
                </tr>
              </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((row) => (
                <tr key={row.id} className="transition-colors hover:bg-slate-50">
                  <td className="whitespace-nowrap px-3 py-2.5 text-xs tabular-nums text-slate-600">
                    {fmtDateTime(row.at)}
                  </td>
                  <td className="px-3 py-2.5">
                    <span className="rounded bg-slate-100 px-2 py-1 font-mono text-xs font-semibold text-slate-800">
                      {row.action}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-slate-700">{row.entity ?? '—'}</td>
                  <td className="px-3 py-2.5 font-mono text-xs text-slate-500" title={row.entity_id ?? undefined}>
                    {row.entity_id ? `${row.entity_id.slice(0, 8)}…` : '—'}
                  </td>
                  <td className="px-3 py-2.5 font-mono text-xs text-slate-500" title={row.user_id ?? undefined}>
                    {row.user_id ? `${row.user_id.slice(0, 8)}…` : '—'}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2.5 font-mono text-xs text-slate-500">{row.ip ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      </Card>
    </div>
  );
}
