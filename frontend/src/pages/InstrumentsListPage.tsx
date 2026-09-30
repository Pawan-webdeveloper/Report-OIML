import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listInstruments } from '../api/instruments';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

const CLASS_STYLE: Record<string, string> = {
  I: 'bg-slate-100 text-slate-800 ring-slate-300',
  II: 'bg-slate-100 text-slate-800 ring-slate-300',
  III: 'bg-slate-100 text-slate-800 ring-slate-300',
  IIII: 'bg-slate-100 text-slate-800 ring-slate-300',
};

export default function InstrumentsListPage() {
  const [q, setQ] = useState('');
  const { data, loading, error, reload } = useAsync(() => listInstruments(q || undefined), [q]);
  const navigate = useNavigate();

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-700">Reference data</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Instrument register</h1>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">Approved instrument models and their metrological capacity ranges.</p>
        </div>
        <Button onClick={() => navigate('/instruments/new')}>New instrument</Button>
      </header>

      <Card>
        <div className="mb-5 flex flex-col gap-3 border-b border-slate-100 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="w-full max-w-sm">
            <Input label="Type designation" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search, for example PS-15K" />
          </div>
          <p className="text-xs tabular-nums text-slate-500" aria-live="polite">
            {loading ? 'Updating register…' : `${data?.length ?? 0} ${data?.length === 1 ? 'instrument' : 'instruments'}`}
          </p>
        </div>

        {loading && (
          <div className="space-y-2" aria-label="Loading instruments">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-12 animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ))}
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <p className="font-semibold">Instrument register could not be loaded</p>
            <p className="mt-1 text-xs">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={reload}>Retry</Button>
          </div>
        )}
        {!loading && !error && data && data.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <p className="text-sm font-semibold text-slate-800">{q ? 'No instruments match this designation' : 'No instruments registered'}</p>
            <p className="mt-1 text-xs text-slate-500">{q ? 'Check the designation or clear the search.' : 'Add the first model to begin the register.'}</p>
          </div>
        )}
        {!loading && !error && data && data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <caption className="sr-only">Registered instrument models</caption>
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                  <th scope="col" className="px-3 py-2.5 font-semibold">Type designation</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Class</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Category</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Capacity</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Verification intervals</th>
                  <th scope="col" className="px-3 py-2.5"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.map((inst) => (
                  <tr key={inst.id} className="transition-colors hover:bg-slate-50">
                    <td className="px-3 py-3 font-semibold text-slate-900">{inst.type_designation}</td>
                    <td className="px-3 py-3">
                      <Badge label={inst.accuracy_class} className={CLASS_STYLE[inst.accuracy_class]} />
                    </td>
                    <td className="px-3 py-3 text-slate-600">{inst.category ?? '—'}</td>
                    <td className="whitespace-nowrap px-3 py-3 tabular-nums text-slate-700">
                      {inst.min_capacity} – {inst.ranges[inst.ranges.length - 1]?.max_capacity} {inst.unit}
                    </td>
                    <td className="px-3 py-3 font-mono text-xs tabular-nums text-slate-600">
                      {inst.ranges.map((r) => `e=${r.e}`).join(' · ')}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <Link to={`/instruments/${inst.id}/edit`} className="rounded px-2 py-1 text-sm font-semibold text-teal-800 hover:bg-teal-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2">
                        Edit
                      </Link>
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
