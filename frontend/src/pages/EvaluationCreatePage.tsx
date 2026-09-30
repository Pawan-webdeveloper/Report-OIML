import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createEvaluation } from '../api/evaluations';
import { listInstruments } from '../api/instruments';
import { apiErrorDetail } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';

export default function EvaluationCreatePage() {
  const instruments = useAsync(() => listInstruments());
  const navigate = useNavigate();
  const [instrumentId, setInstrumentId] = useState('');
  const [purpose, setPurpose] = useState<'TYPE_APPROVAL' | 'VERIFICATION'>('TYPE_APPROVAL');
  const [mpeContext, setMpeContext] = useState<'INITIAL' | 'IN_SERVICE'>('INITIAL');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const ev = await createEvaluation({ instrument_id: instrumentId, purpose, mpe_context: mpeContext });
      navigate(`/evaluations/${ev.id}`);
    } catch (err) {
      setError(apiErrorDetail(err));
      setBusy(false);
    }
  }

  if (instruments.loading) return <Spinner />;

  const selectClass = 'block min-h-12 w-full rounded-lg border-0 bg-white px-3 py-2.5 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500';

  return (
    <div className="space-y-5">
      <div className="border-b border-slate-300 pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-700">Evaluation setup</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">Create type evaluation</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Select the registered instrument and the MPE basis. The required test schedule is generated after creation.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_18rem]">
      <Card title="01 · Evaluation basis">
      <form onSubmit={submit} className="space-y-5">
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-800">Instrument <span className="text-red-700">*</span></label>
          <select
            value={instrumentId}
            onChange={(e) => setInstrumentId(e.target.value)}
            required
            className={selectClass}
          >
            <option value="">— select —</option>
            {(instruments.data ?? []).map((i) => (
              <option key={i.id} value={i.id}>
                {i.type_designation} · Class {i.accuracy_class} · Max {i.ranges[i.ranges.length - 1]?.max_capacity} {i.unit}
              </option>
            ))}
          </select>
          <p className="mt-1.5 text-xs text-slate-500">Only registered instruments can be evaluated.</p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-semibold text-slate-800">Purpose</label>
            <select value={purpose} onChange={(e) => setPurpose(e.target.value as 'TYPE_APPROVAL' | 'VERIFICATION')}
              className={selectClass}>
              <option value="TYPE_APPROVAL">Type approval</option>
              <option value="VERIFICATION">Verification</option>
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-semibold text-slate-800">MPE context</label>
            <select value={mpeContext} onChange={(e) => setMpeContext(e.target.value as 'INITIAL' | 'IN_SERVICE')}
              className={selectClass}>
              <option value="INITIAL">Initial (Table 6)</option>
              <option value="IN_SERVICE">In service (2 × Table 6)</option>
            </select>
          </div>
        </div>

        {error && (
          <div role="alert" className="border-l-4 border-red-600 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
        )}
        <div className="flex flex-wrap items-center gap-3 border-t border-slate-200 pt-5">
          <Button type="submit" loading={busy} disabled={!instrumentId} className="min-h-12">Create evaluation</Button>
          <Button variant="secondary" className="min-h-12" onClick={() => navigate('/evaluations')}>Cancel</Button>
        </div>
      </form>
      </Card>

      <aside className="border border-slate-200 bg-slate-50 p-5 lg:sticky lg:top-5 lg:self-start">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">What happens next</p>
        <ol className="mt-4 space-y-4 text-sm text-slate-700">
          <li className="grid grid-cols-[1.5rem_1fr] gap-2"><span className="font-mono text-slate-400">01</span><span>A report number and required test schedule are created.</span></li>
          <li className="grid grid-cols-[1.5rem_1fr] gap-2"><span className="font-mono text-slate-400">02</span><span>Engineers enter observations and link traceable equipment.</span></li>
          <li className="grid grid-cols-[1.5rem_1fr] gap-2"><span className="font-mono text-slate-400">03</span><span>The completed evaluation is submitted for independent review.</span></li>
        </ol>
      </aside>
      </div>
    </div>
  );
}
