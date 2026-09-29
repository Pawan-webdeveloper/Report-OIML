export interface Party {
  id: string;
  kind: 'MANUFACTURER' | 'APPLICANT' | 'AGENT';
  name: string;
  address: string | null;
  gstin: string | null;
  contact: string | null;
  email: string | null;
}

export interface InstrumentRangeT {
  idx: number;
  e: string;
  d: string;
  max_capacity: string;
}

export interface Instrument {
  id: string;
  application_no: string | null;
  type_designation: string;
  category: string | null;
  accuracy_class: 'I' | 'II' | 'III' | 'IIII';
  indication_type: string;
  display_kind: string | null;
  range_kind: string;
  min_capacity: string;
  unit: string;
  printer: string | null;
  direct_sales_to_public: boolean;
  remarks: string | null;
  ranges: InstrumentRangeT[];
}

export type Verdict = 'PASSED' | 'FAILED' | 'NOT_APPLICABLE' | 'PENDING';

export interface TestRecord {
  id: string;
  evaluation_id: string;
  kind: string;
  form_no: string | null;
  instance_no: number;
  condition_label: string | null;
  test_date: string | null;
  observations: Record<string, unknown>;
  computed: Record<string, unknown> | null;
  verdict: Verdict | null;
  warnings: unknown[] | null;
  remarks: string | null;
}

export interface RequiredTestsPreview {
  required: string[];
  verdicts: Record<string, string>;
  outcome: 'PASS' | 'FAIL' | 'INCOMPLETE';
}

export interface Equipment {
  id: string;
  kind: string;
  name: string | null;
  serial_no: string | null;
  accuracy_class_or_uncertainty: string | null;
}