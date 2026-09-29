import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createEvaluation } from '../api/evaluations';
import { listInstruments } from '../api/instruments';
import { apiErrorDetail } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

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

  return (
    <Card title="New Type Evaluation">
      <form onSubmit={submit} className="max-w-xl space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Instrument *</label>
          <select
            value={instrumentId}
            onChange={(e) => setInstrumentId(e.target.value)}
            required
            className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-primary-500"
          >
            <option value="">— select —</option>
            {(instruments.data ?? []).map((i) => (
              <option key={i.id} value={i.id}>
                {i.type_designation} · Class {i.accuracy_class} · Max {i.ranges[i.ranges.length - 1]?.max_capacity} {i.unit}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Purpose</label>
            <select value={purpose} onChange={(e) => setPurpose(e.target.value as 'TYPE_APPROVAL' | 'VERIFICATION')}
              className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300">
              <option value="TYPE_APPROVAL">Type approval</option>
              <option value="VERIFICATION">Verification</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">MPE context</label>
            <select value={mpeContext} onChange={(e) => setMpeContext(e.target.value as 'INITIAL' | 'IN_SERVICE')}
              className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300">
              <option value="INITIAL">Initial (Table 6)</option>
              <option value="IN_SERVICE">In service (2 × Table 6)</option>
            </select>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" loading={busy} disabled={!instrumentId}>Create evaluation</Button>
      </form>
    </Card>
  );
}