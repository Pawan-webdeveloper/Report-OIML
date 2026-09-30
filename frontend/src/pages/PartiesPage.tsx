import { useState } from 'react';
import { createParty, listParties } from '../api/parties';
import { apiErrorDetail } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';

const KIND_STYLE: Record<string, string> = {
  MANUFACTURER: 'bg-teal-50 text-teal-800 ring-teal-200',
  APPLICANT: 'bg-slate-100 text-slate-800 ring-slate-300',
  AGENT: 'bg-slate-100 text-slate-700 ring-slate-300',
};

export default function PartiesPage() {
  const { data, loading, error, reload } = useAsync(listParties);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [gstin, setGstin] = useState('');
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFormError(null);
    try {
      await createParty({ name, address: address || null, gstin: gstin || null, kind: 'MANUFACTURER' });
      setOpen(false);
      setName('');
      setAddress('');
      setGstin('');
      reload();
    } catch (err) {
      setFormError(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-700">Reference data</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Organisations</h1>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">Manufacturers, applicants, and authorised agents used in evaluation records.</p>
        </div>
        <Button onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="new-party-form">
          {open ? 'Close form' : 'New organisation'}
        </Button>
      </header>

      <Card>
        {open && (
          <form id="new-party-form" onSubmit={submit} className="mb-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-slate-900">Register a manufacturer</h2>
              <p className="mt-1 text-xs text-slate-500">The organisation will be available to new evaluation reports.</p>
            </div>
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
              <Input label="Organisation name" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input label="Registered address" value={address} onChange={(e) => setAddress(e.target.value)} />
              <Input label="GSTIN" value={gstin} onChange={(e) => setGstin(e.target.value)} />
            </div>
            {formError && <p className="mt-3 text-sm text-red-700" role="alert">{formError}</p>}
            <div className="mt-4 flex gap-2">
              <Button type="submit" loading={busy}>Save organisation</Button>
              <Button variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
            </div>
          </form>
        )}

        {loading && (
          <div className="space-y-2" aria-label="Loading organisations">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-12 animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ))}
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <p className="font-semibold">Organisation register could not be loaded</p>
            <p className="mt-1 text-xs">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={reload}>Retry</Button>
          </div>
        )}
        {!loading && !error && data && data.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <p className="text-sm font-semibold text-slate-800">No organisations registered</p>
            <p className="mt-1 text-xs text-slate-500">Register the first manufacturer to use it in evaluations.</p>
            {!open && <Button className="mt-4" onClick={() => setOpen(true)}>New organisation</Button>}
          </div>
        )}
        {!loading && !error && data && data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <caption className="sr-only">Registered manufacturers, applicants, and agents</caption>
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                  <th scope="col" className="px-3 py-2.5 font-semibold">Organisation</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Type</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Registered address</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">GSTIN</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.map((p) => (
                  <tr key={p.id} className="transition-colors hover:bg-slate-50">
                    <td className="px-3 py-3 font-semibold text-slate-900">{p.name}</td>
                    <td className="px-3 py-3"><Badge label={p.kind.replaceAll('_', ' ')} className={KIND_STYLE[p.kind]} /></td>
                    <td className="max-w-md px-3 py-3 text-slate-600">{p.address ?? '—'}</td>
                    <td className="whitespace-nowrap px-3 py-3 font-mono text-xs text-slate-600">{p.gstin ?? '—'}</td>
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
