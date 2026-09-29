import type { D, EngineInstrument, MpeContext } from '../../lib/calc';
import type { Evaluation, Instrument, TestRecord } from '../../types';

export interface TestFormProps {
  evaluation: Evaluation;
  instrument: Instrument;
  engineInst: EngineInstrument;
  resolutionG: D | null;
  mpeContext: MpeContext;
  existing: TestRecord | null;
  readOnly: boolean;
  /** Persists via POST /evaluations/{id}/tests; parent surfaces errors + navigates. */
  onSubmit: (observations: Record<string, unknown>) => Promise<void>;
}