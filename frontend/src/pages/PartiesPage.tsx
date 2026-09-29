import { useState } from 'react';
import { createParty, listParties } from '../api/parties';
import { apiErrorDetail } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';

const KIND_STYLE: Record<string, string> = {
  MANUFACTURER: 'bg-blue-100 text-blue-800 ring-blue-300',
  APPLICANT: 'bg-purple-100 text-purple-800 ring-purple-300',
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
    <Card
      title="Manufacturers & Applicants"
      actions={<Button onClick={() => setOpen(!open)}>{open ? 'Close' : '+ New Party'}</Button>}
    >
      {open && (
        <form onSubmit={submit} className="mb-6 grid grid-cols-1 gap-3 rounded-lg bg-slate-50 p-4 md:grid-cols-3">
          <Input label="Name *" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Address" value={address} onChange={(e) => setAddress(e.target.value)} />
          <Input label="GSTIN" value={gstin} onChange={(e) => setGstin(e.target.value)} />
          <div className="md:col-span-3">
            {formError && <p className="mb-2 text-sm text-red-600">{formError}</p>}
            <Button type="submit" loading={busy}>Save party</Button>
          </div>
        </form>
      )}

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {data && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Kind</th>
                <th className="py-2 pr-4">Address</th>
                <th className="py-2 pr-4">GSTIN</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((p) => (
                <tr key={p.id}>
                  <td className="py-2 pr-4 font-medium">{p.name}</td>
                  <td className="py-2 pr-4"><Badge label={p.kind} className={KIND_STYLE[p.kind]} /></td>
                  <td className="py-2 pr-4 text-slate-600">{p.address ?? '—'}</td>
                  <td className="py-2 pr-4 font-mono text-xs">{p.gstin ?? '—'}</td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr><td colSpan={4} className="py-8 text-center text-slate-500">No parties yet — create one above.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}