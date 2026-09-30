import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listEvaluations } from '../api/evaluations';
import { listInstruments } from '../api/instruments';
import { useAsync } from '../hooks/useAsync';
import type { EvalStatus, Instrument } from '../types';
import { Button } from '../components/ui/Button';
import { fmtDateTime } from '../lib/format';

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  DRAFT: { bg: 'bg-blue-100', text: 'text-blue-700' },
  IN_PROGRESS: { bg: 'bg-amber-100', text: 'text-amber-700' },
  SUBMITTED: { bg: 'bg-purple-100', text: 'text-purple-700' },
  UNDER_REVIEW: { bg: 'bg-purple-100', text: 'text-purple-700' },
  APPROVED: { bg: 'bg-green-100', text: 'text-green-700' },
  ARCHIVED: { bg: 'bg-slate-100', text: 'text-slate-700' },
  RETURNED: { bg: 'bg-red-100', text: 'text-red-700' },
};

export default function DashboardPage() {
  const [filter, setFilter] = useState<EvalStatus | 'ALL'>('ALL');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [page, setPage] = useState(1);
  const [instruments, setInstruments] = useState<Record<string, Instrument>>({});
  const perPage = 8;

  const { data, loading, error, reload } = useAsync(listEvaluations);
  const navigate = useNavigate();

  // Fetch instruments and build a lookup map
  useEffect(() => {
    listInstruments().then(insts => {
      const map: Record<string, Instrument> = {};
      insts.forEach(i => { map[i.id] = i; });
      setInstruments(map);
    }).catch(() => {});
  }, []);

  const evaluations = data ?? [];
  const visible = filter === 'ALL' ? evaluations : evaluations.filter((e) => e.status === filter);
  const totalPages = Math.ceil(visible.length / perPage);
  const paginatedEvals = visible.slice((page - 1) * perPage, page * perPage);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-50">
            <svg className="h-6 w-6 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Evaluations</h1>
            <p className="text-sm text-slate-600">Manage and track instrument evaluations</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <input
              type="text"
              placeholder="Search evaluations..."
              className="w-64 rounded-lg border border-slate-200 bg-white px-4 py-2 pr-10 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
            />
            <svg className="absolute right-3 top-2.5 h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <Button
            variant="primary"
            onClick={() => navigate('/evaluations/new')}
            className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Evaluation
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border border-slate-200 bg-white p-1">
            {(['ALL', 'DRAFT', 'IN_PROGRESS', 'APPROVED'] as const).map((status) => (
              <button
                key={status}
                onClick={() => { setFilter(status); setPage(1); }}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  filter === status ? 'bg-teal-600 text-white' : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                {status === 'ALL' ? 'All' : status.replace('_', ' ')}
              </button>
            ))}
          </div>
          <select className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-teal-500 focus:outline-none">
            <option>All Instruments</option>
          </select>
          <button className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Date Range
          </button>
        </div>

        <div className="flex items-center gap-3">
          <select className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-teal-500 focus:outline-none">
            <option>Sort by: Updated (Newest)</option>
            <option>Sort by: Created (Newest)</option>
            <option>Sort by: Status</option>
          </select>
          <div className="flex rounded-lg border border-slate-200 bg-white">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 ${viewMode === 'grid' ? 'bg-teal-50 text-teal-600' : 'text-slate-400'}`}
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 ${viewMode === 'list' ? 'bg-teal-50 text-teal-600' : 'text-slate-400'}`}
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-64 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          <p className="font-semibold">Evaluations could not be loaded</p>
          <p className="mt-1 text-xs">{error}</p>
          <Button variant="secondary" className="mt-3" onClick={reload}>Retry</Button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && visible.length === 0 && (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-5 py-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-4 text-sm font-semibold text-slate-800">No evaluations found</p>
          <p className="mt-1 text-xs text-slate-500">Create a new evaluation to get started.</p>
          <Button variant="primary" className="mt-4" onClick={() => navigate('/evaluations/new')}>
            Create Evaluation
          </Button>
        </div>
      )}

      {/* Grid View */}
      {!loading && !error && visible.length > 0 && viewMode === 'grid' && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {paginatedEvals.map((ev) => {
            const statusColor = STATUS_COLORS[ev.status] || STATUS_COLORS.DRAFT;
            const progress = ev.status === 'APPROVED' || ev.status === 'ARCHIVED' ? 100 :
              ev.status === 'IN_PROGRESS' ? 60 :
              ev.status === 'DRAFT' ? 25 : 40;
            const step = ev.status === 'DRAFT' ? 1 : ev.status === 'IN_PROGRESS' ? 3 : ev.status === 'SUBMITTED' ? 4 : 5;
            const totalSteps = 5;

            return (
              <div
                key={ev.id}
                onClick={() => navigate(`/evaluations/${ev.id}`)}
                className="group cursor-pointer rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-teal-300 hover:shadow-md"
              >
                <div className="mb-3 flex items-start justify-between">
                  <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${statusColor.bg} ${statusColor.text}`}>
                    {ev.status.replace('_', ' ')}
                  </span>
                  <button className="text-slate-400 hover:text-slate-600">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                  </button>
                </div>

                <div className="mb-3 flex h-24 items-center justify-center rounded-lg bg-slate-50">
                  <svg className="h-16 w-16 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3L7 9H17L15 3H9Z M7 9L5 15H19L17 9H7Z M12 18v3 M10 21h4" />
                  </svg>
                </div>

                <div className="mb-3">
                  <h3 className="text-sm font-semibold text-slate-900">
                    {instruments[ev.instrument_id]?.type_designation || 'Instrument'}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {instruments[ev.instrument_id]?.category || 'Weighing Instrument'}
                  </p>
                </div>

                <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-slate-500">Report No.</p>
                    <p className="font-mono font-semibold text-teal-700">{ev.report_no}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Updated</p>
                    <p className="font-medium text-slate-700">{fmtDateTime(ev.created_at).split(',')[0]}</p>
                  </div>
                </div>

                <div className="mb-2">
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="text-slate-500">Step {step} of {totalSteps}</span>
                    <span className={`font-semibold ${progress === 100 ? 'text-green-600' : 'text-teal-600'}`}>
                      {progress}%
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full transition-all ${progress === 100 ? 'bg-green-500' : 'bg-teal-500'}`}
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>

                {progress === 100 && (
                  <p className="text-xs font-medium text-green-600">Completed</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* List View */}
      {!loading && !error && visible.length > 0 && viewMode === 'list' && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">Report No.</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">Status</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">Instrument</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">Updated</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">Progress</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paginatedEvals.map((ev) => {
                const statusColor = STATUS_COLORS[ev.status] || STATUS_COLORS.DRAFT;
                const progress = ev.status === 'APPROVED' ? 100 : ev.status === 'IN_PROGRESS' ? 60 : 25;

                return (
                  <tr key={ev.id} className="cursor-pointer transition-colors hover:bg-slate-50" onClick={() => navigate(`/evaluations/${ev.id}`)}>
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-teal-700">{ev.report_no}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-md px-2 py-1 text-xs font-semibold ${statusColor.bg} ${statusColor.text}`}>
                        {ev.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">{instruments[ev.instrument_id]?.type_designation || 'Instrument'}</p>
                      <p className="text-xs text-slate-500">{instruments[ev.instrument_id]?.category || 'Weighing Instrument'}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600">{fmtDateTime(ev.created_at).split(',')[0]}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
                          <div className={`h-full rounded-full ${progress === 100 ? 'bg-green-500' : 'bg-teal-500'}`} style={{ width: `${progress}%` }} />
                        </div>
                        <span className="text-xs font-semibold text-slate-600">{progress}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button className="text-slate-400 hover:text-slate-600">
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {visible.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-600">
            Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, visible.length)} of {visible.length} evaluations
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`rounded-lg px-3 py-2 text-sm font-medium ${
                  p === page ? 'bg-teal-600 text-white' : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                {p}
              </button>
            ))}
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">Show</span>
            <select className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-sm">
              <option>8</option>
              <option>16</option>
              <option>32</option>
            </select>
            <span className="text-sm text-slate-600">per page</span>
          </div>
        </div>
      )}
    </div>
  );
}
