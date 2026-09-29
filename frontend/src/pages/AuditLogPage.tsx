import { useState } from 'react';
import { listAudit } from '../api/admin';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Spinner } from '../components/ui/Spinner';
import { fmtDateTime } from '../lib/format';

export default function AuditLogPage() {
  const [action, setAction] = useState('');
  const [entity, setEntity] = useState('');
  const { data, loading, error } = useAsync(
    () => listAudit({ action: action || undefined, entity: entity || undefined, limit: 200 }),
    [action, entity],
  );

  return (
    <Card title="Audit trail — who did what, when (immutable)">
      <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <Input label="Filter by action" value={action}
          onChange={(e) => setAction(e.target.value)}
          placeholder="e.g. EVALUATION, LOGIN, TEST_RECORD" />
        <Input label="Filter by entity" value={entity}
          onChange={(e) => setEntity(e.target.value)}
          placeholder="e.g. evaluation, user, attachment" />
        <p className="self-end pb-2 text-xs text-slate-500">
          Showing the latest {data?.length ?? 0} entries (server-side filter).
        </p>
      </div>

      {loading && <Spinner />}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {data && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Action</th>
                <th className="py-2 pr-4">Entity</th>
                <th className="py-2 pr-4">Entity ID</th>
                <th className="py-2 pr-4">User</th>
                <th className="py-2">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50">
                  <td className="py-2 pr-4 whitespace-nowrap text-slate-600">
                    {fmtDateTime(row.at)}
                  </td>
                  <td className="py-2 pr-4">
                    <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs font-medium text-slate-800">
                      {row.action}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-slate-600">{row.entity ?? '—'}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-slate-500">
                    {row.entity_id ? `${row.entity_id.slice(0, 8)}…` : '—'}
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs text-slate-500">
                    {row.user_id ? `${row.user_id.slice(0, 8)}…` : '—'}
                  </td>
                  <td className="py-2 font-mono text-xs text-slate-500">{row.ip ?? '—'}</td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr><td colSpan={6} className="py-10 text-center text-slate-500">No audit entries match.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}