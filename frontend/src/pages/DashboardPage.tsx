import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { getKpis } from '../api/dashboard';
import { listEvaluations } from '../api/evaluations';
import { useAsync } from '../hooks/useAsync';
import type { EvalStatus } from '../types';
import { Card, KpiCard } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge, OutcomeBadge, StatusBadge } from '../components/ui/Badge';
import { fmtDateTime } from '../lib/format';
import { useAuthStore } from '../store/authStore';

const FILTERS: { key: EvalStatus | 'ALL'; label: string }[] = [
  { key: 'ALL', label: 'All' },
  { key: 'DRAFT', label: 'Draft' },
  { key: 'IN_PROGRESS', label: 'In Progress' },
  { key: 'SUBMITTED', label: 'Submitted' },
  { key: 'UNDER_REVIEW', label: 'Under Review' },
  { key: 'APPROVED', label: 'Approved' },
];

const shortKind = (k: string) => (k.length > 14 ? `${k.slice(0, 13)}…` : k);

const initials = (name: string) =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('') || '?';

export default function DashboardPage() {
  const [filter, setFilter] = useState<EvalStatus | 'ALL'>('ALL');
  const kpis = useAsync(getKpis);
  const { data, loading, error, reload } = useAsync(listEvaluations);
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const k = kpis.data;
  const sc = k?.status_counts ?? {};
  const inFlight = (sc.DRAFT ?? 0) + (sc.IN_PROGRESS ?? 0) + (sc.RETURNED ?? 0);
  const inReview = (sc.SUBMITTED ?? 0) + (sc.UNDER_REVIEW ?? 0);
  const approved = (sc.APPROVED ?? 0) + (sc.ARCHIVED ?? 0);

  const evaluations = data ?? [];
  const visible =
    filter === 'ALL' ? evaluations : evaluations.filter((e) => e.status === filter);

  const stats = useMemo(
    () => (k ? [
      { label: 'Instruments registered', value: k.totals.instruments },
      { label: 'Test pages recorded', value: k.totals.test_records },
      { label: 'Portal users', value: k.totals.users },
      { label: 'Failed tests (all time)', value: k.failures.reduce((a, f) => a + f.count, 0) },
    ] : []),
    [k],
  );

  return (
    <div className="space-y-6">
      {/* Signed-in user */}
      {user && (
        <div className="rounded-xl border border-primary-700 bg-gradient-to-br from-primary-700 to-primary-900 p-5 shadow-sm">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white/15 text-lg font-semibold text-white">
              {initials(user.full_name || user.username)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium uppercase tracking-wide text-primary-200">
                Signed in as
              </p>
              <p className="truncate text-xl font-semibold text-white">
                {user.full_name || user.username}
              </p>
              <p className="truncate text-sm text-primary-100">
                @{user.username} · {user.email}
              </p>
            </div>
            <Badge label={user.role} className="bg-white/15 text-white ring-white/30" />
          </div>
        </div>
      )}

      {/* KPI cards (server-side) */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard label="Total Reports" value={k?.totals.evaluations ?? '…'} />
        <KpiCard label="In Progress" value={inFlight} tone="blue" />
        <KpiCard label="Under Review" value={inReview} tone="amber" />
        <KpiCard label="Approved / Archived" value={approved} tone="emerald" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Evaluations created — last 6 months">
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={k?.trend ?? []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" fontSize={11} tickLine={false} />
                <YAxis allowDecimals={false} fontSize={11} width={28} tickLine={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Failure analysis — FAILED verdicts by test">
          <div className="h-44">
            {(k?.failures.length ?? 0) === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-500">
                🎉 No failed tests recorded yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={k?.failures ?? []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" allowDecimals={false} fontSize={11} tickLine={false} />
                  <YAxis type="category" dataKey="kind" width={110} fontSize={10}
                    tickFormatter={shortKind} tickLine={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#dc2626" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      {/* Small stats strip */}
      {stats.length > 0 && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label}
              className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm">
              <p className="text-xs text-slate-500">{s.label}</p>
              <p className="mt-0.5 text-lg font-semibold text-slate-800">{s.value}</p>
            </div>
          ))}
        </div>
      )}

      <Card
        title="Type Evaluation Reports"
        actions={
          <Button variant="secondary" onClick={reload} disabled={loading}>
            ↻ Refresh
          </Button>
        }
      >
        <div className="mb-4 flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button key={f.key} onClick={() => setFilter(f.key)}
              className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition ${
                filter === f.key
                  ? 'bg-primary-600 text-white ring-primary-600'
                  : 'bg-white text-slate-600 ring-slate-300 hover:bg-slate-50'
              }`}>
              {f.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-inset ring-red-200">
            <p className="font-medium">Failed to load evaluations</p>
            <p className="mt-1 text-xs">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={reload}>Retry</Button>
          </div>
        )}

        {loading && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-slate-100" />
            ))}
          </div>
        )}

        {!loading && !error && visible.length === 0 && (
          <div className="py-12 text-center">
            <p className="text-4xl">🗂️</p>
            <p className="mt-3 text-sm font-medium text-slate-700">No evaluations found</p>
          </div>
        )}

        {!loading && !error && visible.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-semibold">Report No.</th>
                  <th className="py-2 pr-4 font-semibold">Status</th>
                  <th className="py-2 pr-4 font-semibold">Outcome</th>
                  <th className="py-2 pr-4 font-semibold">Purpose</th>
                  <th className="py-2 pr-4 font-semibold">Created</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visible.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50">
                    <td className="py-3 pr-4 font-mono text-xs font-medium text-primary-700">
                      {ev.report_no}
                    </td>
                    <td className="py-3 pr-4"><StatusBadge status={ev.status} /></td>
                    <td className="py-3 pr-4">
                      {ev.outcome
                        ? <OutcomeBadge outcome={ev.outcome} />
                        : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="py-3 pr-4 text-slate-600">{ev.purpose.replaceAll('_', ' ')}</td>
                    <td className="py-3 pr-4 text-slate-500">{fmtDateTime(ev.created_at)}</td>
                    <td className="py-3 text-right">
                      <Button variant="ghost" onClick={() => navigate(`/evaluations/${ev.id}`)}>
                        View
                      </Button>
                    </td>
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