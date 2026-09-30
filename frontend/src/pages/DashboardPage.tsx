import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { getKpis } from '../api/dashboard';
import { listEvaluations } from '../api/evaluations';
import { useAsync } from '../hooks/useAsync';
import type { EvalStatus } from '../types';
import { Card } from '../components/ui/Card';
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
    <div className="space-y-5">
      {user && (
        <section className="rounded-xl border border-slate-800 bg-slate-900 px-5 py-4 text-white shadow-sm" aria-label="Signed-in account">
          <div className="flex flex-wrap items-center gap-3 sm:gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-sm font-semibold tracking-wide text-slate-100" aria-hidden="true">
              {initials(user.full_name || user.username)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                Active account
              </p>
              <p className="mt-0.5 truncate text-base font-semibold text-white">
                {user.full_name || user.username}
              </p>
              <p className="truncate text-xs text-slate-400">
                @{user.username} · {user.email}
              </p>
            </div>
            <Badge label={user.role} className="bg-slate-800 text-slate-200 ring-slate-600" />
          </div>
        </section>
      )}

      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-700">Operations overview</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Evaluation control desk</h1>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">Current workload, review progress, and recorded test outcomes.</p>
        </div>
        <p className="text-xs text-slate-500">Live system totals</p>
      </div>

      {kpis.error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          <p className="font-semibold">Dashboard totals are unavailable</p>
          <p className="mt-1 text-xs">{kpis.error}</p>
          <Button variant="secondary" className="mt-3" onClick={kpis.reload}>Retry totals</Button>
        </div>
      )}

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="Evaluation summary">
        {[
          { label: 'Total reports', value: k?.totals.evaluations, valueClass: 'text-slate-950' },
          { label: 'In progress', value: k ? inFlight : undefined, valueClass: 'text-teal-800' },
          { label: 'Under review', value: k ? inReview : undefined, valueClass: 'text-amber-700' },
          { label: 'Approved or archived', value: k ? approved : undefined, valueClass: 'text-emerald-700' },
        ].map((item) => (
          <div key={item.label} className="min-w-0 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm sm:px-5">
            <p className="text-xs font-medium leading-4 text-slate-500">{item.label}</p>
            {kpis.loading ? (
              <div className="mt-3 h-8 w-16 animate-pulse rounded bg-slate-100 motion-reduce:animate-none" />
            ) : (
              <p className={`mt-2 text-2xl font-semibold tabular-nums tracking-tight sm:text-3xl ${item.valueClass}`}>{item.value ?? '—'}</p>
            )}
          </div>
        ))}
      </section>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card title="Evaluation volume · last 6 months">
          <div className="h-52" aria-label="Evaluations created by month">
            {kpis.loading ? (
              <div className="h-full animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ) : (k?.trend.length ?? 0) === 0 ? (
              <div className="flex h-full flex-col items-center justify-center px-5 text-center">
                <p className="text-sm font-medium text-slate-700">No evaluation volume recorded</p>
                <p className="mt-1 text-xs text-slate-500">Monthly activity will appear after reports are created.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={k?.trend ?? []}>
                  <CartesianGrid vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="month" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis allowDecimals={false} fontSize={11} width={28} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#0f766e" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        <Card title="Failure analysis · failed verdicts by test">
          <div className="h-52">
            {kpis.loading ? (
              <div className="h-full animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ) : (k?.failures.length ?? 0) === 0 ? (
              <div className="flex h-full flex-col items-center justify-center px-5 text-center">
                <p className="text-sm font-medium text-slate-700">No failed tests recorded</p>
                <p className="mt-1 text-xs text-slate-500">Failure counts will appear here when a test receives a failed verdict.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={k?.failures ?? []} layout="vertical">
                  <CartesianGrid horizontal={false} stroke="#e2e8f0" />
                  <XAxis type="number" allowDecimals={false} fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="kind" width={110} fontSize={10}
                    tickFormatter={shortKind} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#b91c1c" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      {stats.length > 0 && (
        <section className="grid grid-cols-2 overflow-hidden rounded-xl border border-slate-200 bg-white lg:grid-cols-4" aria-label="Registry totals">
          {stats.map((s) => (
            <div key={s.label}
              className="border-b border-r border-slate-200 px-4 py-3 text-sm last:border-r-0 lg:border-b-0">
              <p className="text-xs leading-4 text-slate-500">{s.label}</p>
              <p className="mt-1 text-lg font-semibold tabular-nums text-slate-900">{s.value}</p>
            </div>
          ))}
        </section>
      )}

      <Card
        title="Recent type evaluation reports"
        actions={
          <Button variant="secondary" onClick={reload} disabled={loading}>
            Refresh
          </Button>
        }
      >
        <div className="mb-4 flex flex-wrap gap-2" aria-label="Filter reports by status">
          {FILTERS.map((f) => (
            <button key={f.key} type="button" aria-pressed={filter === f.key} onClick={() => setFilter(f.key)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2 ${
                filter === f.key
                  ? 'bg-slate-900 text-white ring-slate-900'
                  : 'bg-white text-slate-600 ring-slate-300 hover:bg-slate-50'
              }`}>
              {f.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <p className="font-semibold">Reports could not be loaded</p>
            <p className="mt-1 text-xs">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={reload}>Retry</Button>
          </div>
        )}

        {loading && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ))}
          </div>
        )}

        {!loading && !error && visible.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <p className="text-sm font-semibold text-slate-800">No reports in this view</p>
            <p className="mt-1 text-xs text-slate-500">Choose another status to review the full register.</p>
          </div>
        )}

        {!loading && !error && visible.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] text-left text-sm">
              <caption className="sr-only">Type evaluation reports</caption>
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                  <th scope="col" className="px-3 py-2.5 font-semibold">Report no.</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Status</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Outcome</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Purpose</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Created</th>
                  <th scope="col" className="px-3 py-2.5"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visible.map((ev) => (
                  <tr key={ev.id} className="transition-colors hover:bg-slate-50">
                    <td className="px-3 py-3 font-mono text-xs font-semibold tabular-nums text-teal-800">
                      {ev.report_no}
                    </td>
                    <td className="px-3 py-3"><StatusBadge status={ev.status} /></td>
                    <td className="px-3 py-3">
                      {ev.outcome
                        ? <OutcomeBadge outcome={ev.outcome} />
                        : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-3 text-slate-600">{ev.purpose.replaceAll('_', ' ')}</td>
                    <td className="whitespace-nowrap px-3 py-3 text-xs tabular-nums text-slate-500">{fmtDateTime(ev.created_at)}</td>
                    <td className="px-3 py-3 text-right">
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
