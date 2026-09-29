import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createInstrument, getInstrument, type RangePayload } from '../api/instruments';
import { listParties } from '../api/parties';
import { apiErrorDetail } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { useAuthStore } from '../store/authStore';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Spinner } from '../components/ui/Spinner';
import { validateInstrumentLive, type AccuracyClass } from '../lib/calc';

const EMPTY_RANGE: RangePayload = { e: '', d: '', max: '' };

export default function InstrumentFormPage({ mode }: { mode: 'create' | 'edit' }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const role = useAuthStore((s) => s.user?.role);

  const parties = useAsync(listParties);
  const existing = useAsync(
    async () => (mode === 'edit' && id ? getInstrument(id) : null),
    [mode, id],
  );

  const [typeDesignation, setTypeDesignation] = useState('');
  const [applicationNo, setApplicationNo] = useState('');
  const [category, setCategory] = useState('');
  const [manufacturerId, setManufacturerId] = useState('');
  const [accuracyClass, setAccuracyClass] = useState<AccuracyClass>('III');
  const [unit, setUnit] = useState('kg');
  const [minCapacity, setMinCapacity] = useState('');
  const [mainsAc, setMainsAc] = useState(true);
  const [printer, setPrinter] = useState('NOT_PRESENT_CONNECTABLE');
  const [directSales, setDirectSales] = useState(false);
  const [zeroTracking, setZeroTracking] = useState(true);
  const [tareSubtractive, setTareSubtractive] = useState(true);
  const [ranges, setRanges] = useState<RangePayload[]>([{ ...EMPTY_RANGE }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  // Hydrate the form once the existing instrument arrives (edit mode).
  if (mode === 'edit' && existing.data && !hydrated) {
    const inst = existing.data;
    setTypeDesignation(inst.type_designation);
    setApplicationNo(inst.application_no ?? '');
    setCategory(inst.category ?? '');
    setAccuracyClass(inst.accuracy_class);
    setUnit(inst.unit);
    setMinCapacity(inst.min_capacity);
    setRanges(inst.ranges.map((r) => ({ e: r.e, d: r.d, max: r.max_capacity })));
    setHydrated(true);
  }

  const live = useMemo(
    () =>
      minCapacity && ranges.every((r) => r.e && r.d && r.max)
        ? validateInstrumentLive(accuracyClass, minCapacity, unit, ranges)
        : { errors: [], warnings: [] },
    [accuracyClass, minCapacity, unit, ranges],
  );

  const canSave =
    typeDesignation.trim().length > 0 &&
    minCapacity.trim().length > 0 &&
    ranges.length > 0 &&
    ranges.every((r) => r.e && r.d && r.max) &&
    live.errors.length === 0 &&
    (role === 'ADMIN' || role === 'ENGINEER');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const body = {
      type_designation: typeDesignation.trim(),
      application_no: applicationNo || null,
      category: category || null,
      manufacturer_id: manufacturerId || null,
      accuracy_class: accuracyClass,
      unit,
      min_capacity: minCapacity,
      power_supply_category: mainsAc ? ['MAINS_AC'] : [],
      printer,
      direct_sales_to_public: directSales,
      level_indicator: true,
      zero_devices: { tracking: zeroTracking, initial: true },
      tare_devices: { subtractive: tareSubtractive },
      ranges,
    };
    try {
      if (mode === 'create') {
        await createInstrument(body);
        navigate('/instruments');
      } else if (id) {
        await import('../api/instruments').then((m) => m.updateInstrument(id, body));
        navigate('/instruments');
      }
    } catch (err) {
      setError(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  if ((mode === 'edit' && existing.loading) || parties.loading) return <Spinner />;
  if (mode === 'edit' && existing.error) return <p className="text-sm text-red-600">{existing.error}</p>;

  return (
    <form onSubmit={submit} className="space-y-6">
      <Card title={mode === 'create' ? 'Register instrument (R 76-2 General Information)' : `Edit — ${existing.data?.type_designation ?? ''}`}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Input label="Type designation *" value={typeDesignation} onChange={(e) => setTypeDesignation(e.target.value)} required />
          <Input label="Application no." value={applicationNo} onChange={(e) => setApplicationNo(e.target.value)} />
          <Input label="Category" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Platform scale / Weighbridge…" />

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Manufacturer</label>
            <select
              value={manufacturerId}
              onChange={(e) => setManufacturerId(e.target.value)}
              className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-primary-500"
            >
              <option value="">— none —</option>
              {(parties.data ?? []).map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <p className="mt-1 text-xs text-slate-500">Missing? Add it under Manufacturers first.</p>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Accuracy class *</label>
            <select
              value={accuracyClass}
              onChange={(e) => setAccuracyClass(e.target.value as AccuracyClass)}
              className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-primary-500"
            >
              {(['I', 'II', 'III', 'IIII'] as AccuracyClass[]).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Unit *</label>
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-primary-500"
            >
              {['kg', 'g', 'mg', 't', 'ct'].map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
            <p className="mt-1 text-xs text-slate-500">Tip: use <b>g</b> for the cleanest test-entry demo.</p>
          </div>

          <Input label={`Min capacity (${unit}) *`} value={minCapacity} onChange={(e) => setMinCapacity(e.target.value)} placeholder="0.1" required />

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Printer</label>
            <select value={printer} onChange={(e) => setPrinter(e.target.value)}
              className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-primary-500">
              <option value="NOT_PRESENT_CONNECTABLE">Not present (connectable)</option>
              <option value="BUILT_IN">Built-in</option>
              <option value="CONNECTED">Connected</option>
              <option value="NO_CONNECTION">No connection</option>
            </select>
          </div>
        </div>

        <fieldset className="mt-5 flex flex-wrap gap-5 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={mainsAc} onChange={(e) => setMainsAc(e.target.checked)} className="h-4 w-4" />
            AC mains powered (electronic)
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={zeroTracking} onChange={(e) => setZeroTracking(e.target.checked)} className="h-4 w-4" />
            Zero-tracking device
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={tareSubtractive} onChange={(e) => setTareSubtractive(e.target.checked)} className="h-4 w-4" />
            Subtractive tare
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={directSales} onChange={(e) => setDirectSales(e.target.checked)} className="h-4 w-4" />
            Direct sales to public
          </label>
        </fieldset>
      </Card>

      <Card title="Weighing ranges (e, d, Max)">
        <div className="space-y-3">
          {ranges.map((r, i) => (
            <div key={i} className="grid grid-cols-4 items-end gap-3">
              <Input label={`Range ${i + 1} — e (${unit}) *`} value={r.e}
                onChange={(e) => setRanges(ranges.map((x, j) => (j === i ? { ...x, e: e.target.value } : x)))} />
              <Input label={`d (${unit}) *`} value={r.d}
                onChange={(e) => setRanges(ranges.map((x, j) => (j === i ? { ...x, d: e.target.value } : x)))} />
              <Input label={`Max (${unit}) *`} value={r.max}
                onChange={(e) => setRanges(ranges.map((x, j) => (j === i ? { ...x, max: e.target.value } : x)))} />
              <Button
                variant="danger"
                onClick={() => setRanges(ranges.filter((_, j) => j !== i))}
                disabled={ranges.length === 1}
              >
                Remove
              </Button>
            </div>
          ))}
          <Button variant="secondary" onClick={() => setRanges([...ranges, { ...EMPTY_RANGE }])}>
            + Add range (multi-interval)
          </Button>
        </div>

        {/* Live OIML Table 3 validation */}
        <div className="mt-5 rounded-lg border border-slate-200 p-4">
          <p className="mb-2 text-sm font-semibold text-slate-700">OIML R 76-1 Table 3 — live compliance</p>
          {live.errors.length === 0 && live.warnings.length === 0 && ranges.every((r) => r.e && r.d && r.max) && (
            <p className="text-sm font-medium text-emerald-700">✓ Compliant — classification valid.</p>
          )}
          {live.errors.map((v) => (
            <p key={v.code} className="text-sm text-red-700">✗ {v.message}</p>
          ))}
          {live.warnings.map((v) => (
            <p key={v.code} className="text-sm text-amber-700">⚠ {v.message}</p>
          ))}
        </div>
      </Card>

      {error && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-inset ring-red-200">{error}</div>
      )}

      <div className="flex gap-3">
        <Button type="submit" loading={busy} disabled={!canSave}>
          {mode === 'create' ? 'Create instrument' : 'Save changes'}
        </Button>
        <Button variant="secondary" onClick={() => navigate('/instruments')}>Cancel</Button>
      </div>
    </form>
  );
}