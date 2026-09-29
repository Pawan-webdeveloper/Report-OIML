import { useMemo } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { saveTestRecord } from '../../api/tests';
import { getInstrument } from '../../api/instruments';
import { apiErrorDetail } from '../../api/client';
import { useAsync } from '../../hooks/useAsync';
import { useAuthStore } from '../../store/authStore';
import { getEvaluation } from '../../api/evaluations';
import { listTestRecords } from '../../api/tests';
import { Card } from '../../components/ui/Card';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import { VerdictBadge } from '../../components/data-display/PassFailBadge';
import { buildEngineInstrument, fromBase, type EngineInstrument, type MpeContext } from '../../lib/calc';
import { testFormNo, testTitle } from '../../lib/testmeta';
import type { TestFormProps } from './types';
import WeighingForm from './WeighingForm';
import EccentricityForm from './EccentricityForm';
import RepeatabilityForm from './RepeatabilityForm';
import { CreepForm, ZeroReturnForm } from './SimpleTests';
import JsonFallbackForm from './JsonFallbackForm';

const EDITABLE = ['DRAFT', 'IN_PROGRESS', 'RETURNED'];

const REGISTRY: Record<string, React.ComponentType<TestFormProps>> = {
  WEIGHING: WeighingForm,
  TARE: WeighingForm,          // same observation structure (net loads)
  VOLTAGE: WeighingForm,       // one page per voltage instance
  DAMP_HEAT: WeighingForm,     // one page per phase
  ECC_WEIGHTS: EccentricityForm,
  ECC_ROLLING: EccentricityForm,
  REPEATABILITY: RepeatabilityForm,
  ZERO_RETURN: ZeroReturnForm,
  CREEP: CreepForm,
};

export default function TestEntryPage() {
  const { id = '', kind = '', instanceNo = '1' } = useParams();
  const kindU = kind.toUpperCase();
  const instance = Number(instanceNo) || 1;
  const navigate = useNavigate();
  const role = useAuthStore((s) => s.user?.role);

  const evaluation = useAsync(() => getEvaluation(id), [id]);
  const instId = evaluation.data?.instrument_id ?? null;
  const instrument = useAsync(async () => (instId ? getInstrument(instId) : null), [instId]);
  const records = useAsync(() => listTestRecords(id), [id]);

  const engineInst: EngineInstrument | null = useMemo(() => {
    if (!instrument.data) return null;
    const i = instrument.data;
    try {
      return buildEngineInstrument(
        i.accuracy_class, i.min_capacity, i.unit,
        i.ranges.map((r) => ({ e: r.e, d: r.d, max: r.max_capacity })),
      );
    } catch {
      return null;
    }
  }, [instrument.data]);

  const existing = (records.data ?? []).find((r) => r.kind === kindU && r.instance_no === instance) ?? null;

  if (evaluation.loading || instrument.loading || records.loading) return <Spinner />;
  if (evaluation.error || !evaluation.data) return <p className="text-sm text-red-600">{evaluation.error}</p>;
  if (!instrument.data || !engineInst) return <p className="text-sm text-red-600">Could not build the engine instrument (check ranges).</p>;

  const ev = evaluation.data;
  const readOnly =
    !EDITABLE.includes(ev.status) || role !== 'ENGINEER';

  // Engine resolution = the range's d (already in base grams).
  const resolutionG = engineInst.ranges[0].d;

  async function handleSubmit(observations: Record<string, unknown>) {
    try {
      await saveTestRecord(id, {
        kind: kindU,
        instance_no: instance,
        observations,
      });
      navigate(`/evaluations/${id}`);
    } catch (err) {
      // surface via window for simplicity; parent page shows banners elsewhere
      alert(apiErrorDetail(err));
    }
  }

  const Form = REGISTRY[kindU] ?? JsonFallbackForm;

  return (
    <div className="space-y-5">
      <Card
        title={`Form ${testFormNo(kindU)} — ${testTitle(kindU)}${instance > 1 ? ` (page ${instance})` : ''}`}
        actions={<VerdictBadge verdict={existing?.verdict} />}
      >
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
          <div>
            <p className="font-medium text-slate-800">
              {instrument.data.type_designation} · Class {instrument.data.accuracy_class} ·{' '}
              {ev.report_no}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              e = <b className="font-mono">{fmtE(engineInst, instrument.data.unit)}</b> {instrument.data.unit} ·
              {' '}Max = {instrument.data.ranges[instrument.data.ranges.length - 1]?.max_capacity} {instrument.data.unit} ·
              {' '}step during test = <b className="font-mono">{resolutionG ? resolutionG.div(engineInst.ranges[0].d.toNumber() ? 1 : 1).toString() : '—'}</b>
            </p>
          </div>
          <div className="flex items-center gap-3">
            {readOnly && (
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-300">
                {ev.status === 'SUBMITTED' || ev.status === 'UNDER_REVIEW' || ev.status === 'APPROVED' || ev.status === 'ARCHIVED'
                  ? 'Read-only — evaluation is past the entry stage'
                  : 'Read-only for your role'}
              </span>
            )}
            <Link to={`/evaluations/${id}`}>
              <Button variant="secondary">← Back to evaluation</Button>
            </Link>
          </div>
        </div>
      </Card>

      <Card>
        <Form
          evaluation={ev}
          instrument={instrument.data}
          engineInst={engineInst}
          resolutionG={resolutionG}
          mpeContext={ev.mpe_context as MpeContext}
          existing={existing}
          readOnly={readOnly}
          onSubmit={handleSubmit}
        />
      </Card>
    </div>
  );
}

function fmtE(inst: EngineInstrument, unit: string): string {
  return fromBase(inst.smallestE, unit).toString();
}