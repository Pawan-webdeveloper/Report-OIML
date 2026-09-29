import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listInstruments } from '../api/instruments';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

const CLASS_STYLE: Record<string, string> = {
  I: 'bg-purple-100 text-purple-800 ring-purple-300',
  II: 'bg-blue-100 text-blue-800 ring-blue-300',
  III: 'bg-emerald-100 text-emerald-800 ring-emerald-300',
  IIII: 'bg-amber-100 text-amber-800 ring-amber-300',
};

export default function InstrumentsListPage() {
  const [q, setQ] = useState('');
  const { data, loading, error } = useAsync(() => listInstruments(q || undefined), [q]);
  const navigate = useNavigate();

  return (
    <Card
      title="Instruments & Models"
      actions={
        <Button onClick={() => navigate('/instruments/new')}>+ New Instrument</Button>
      }
    >
      <div className="mb-4 max-w-sm">
        <Input label="Search by type designation" value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. PS-15K" />
      </div>

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {data && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="py-2 pr-4">Type designation</th>
                <th className="py-2 pr-4">Class</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Min / Max</th>
                <th className="py-2 pr-4">Ranges (e, d, Max)</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((inst) => (
                <tr key={inst.id} className="hover:bg-slate-50">
                  <td className="py-2 pr-4 font-medium">{inst.type_designation}</td>
                  <td className="py-2 pr-4">
                    <Badge label={inst.accuracy_class} className={CLASS_STYLE[inst.accuracy_class]} />
                  </td>
                  <td className="py-2 pr-4 text-slate-600">{inst.category ?? '—'}</td>
                  <td className="py-2 pr-4 text-slate-600">
                    {inst.min_capacity} – {inst.ranges[inst.ranges.length - 1]?.max_capacity} {inst.unit}
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs text-slate-500">
                    {inst.ranges.map((r) => `e=${r.e}`).join(' · ')}
                  </td>
                  <td className="py-2 text-right">
                    <Link to={`/instruments/${inst.id}/edit`} className="text-sm font-medium text-primary-700 hover:underline">
                      Edit
                    </Link>
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr><td colSpan={6} className="py-8 text-center text-slate-500">No instruments found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}