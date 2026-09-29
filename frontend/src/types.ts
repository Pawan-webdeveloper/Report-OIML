/** Shared domain types — mirror of the backend Pydantic response models. */

export type Role = 'ADMIN' | 'ENGINEER' | 'REVIEWER' | 'VIEWER';

export type EvalStatus =
  | 'DRAFT'
  | 'IN_PROGRESS'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'RETURNED'
  | 'APPROVED'
  | 'ARCHIVED';

export type Outcome = 'PASS' | 'FAIL' | 'INCOMPLETE';

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: Role;
  is_active: boolean;
  must_change_password: boolean;
}

export interface Range {
  idx: number;
  e: string;
  d: string;
  max_capacity: string;
}

export interface Instrument {
  id: string;
  application_no: string | null;
  type_designation: string;
  manufacturer_id: string | null;
  applicant_id: string | null;
  category: string | null;
  accuracy_class: 'I' | 'II' | 'III' | 'IIII';
  indication_type: string;
  display_kind: string | null;
  range_kind: string;
  min_capacity: string;
  unit: string;
  tare_plus: string | null;
  tare_minus: string | null;
  temp_min_c: string | null;
  temp_max_c: string | null;
  power_supply_category: string[] | null;
  zero_devices: Record<string, boolean> | null;
  tare_devices: Record<string, boolean> | null;
  printer: string | null;
  direct_sales_to_public: boolean;
  remarks: string | null;
  created_at: string;
  ranges: Range[];
}

export interface Evaluation {
  id: string;
  report_no: string;
  instrument_id: string;
  laboratory_id: string;
  range_index: number | null;
  ruleset_id: string;
  purpose: string;
  mpe_context: string;
  status: EvalStatus;
  outcome: Outcome | null;
  observer_id: string | null;
  created_at: string;
  submitted_at: string | null;
  approved_at: string | null;
  approval_hash: string | null;
}

export interface TestRecord {
  id: string;
  evaluation_id: string;
  kind: string;
  form_no: string | null;
  instance_no: number;
  condition_label: string | null;
  test_date: string | null;
  environment: Record<string, unknown> | null;
  observations: Record<string, unknown>;
  computed: Record<string, unknown> | null;
  verdict: string | null;
  warnings: { severity?: string; code?: string; message?: string }[] | null;
  remarks: string | null;
}

export interface RequiredTestsPreview {
  required: string[];
  verdicts: Record<string, string>;
  outcome: Outcome;
}

export interface Equipment {
  id: string;
  kind: string;
  name: string | null;
  model: string | null;
  serial_no: string | null;
  accuracy_class_or_uncertainty: string | null;
  cert_no: string | null;
  calibrated_on: string | null;
  valid_until: string | null;
  weight_nominal: string | null;
  weight_error: string | null;
  weight_uncertainty: string | null;
}

export interface Party {
  id: string;
  kind: string;
  name: string;
  address: string | null;
  gstin: string | null;
  contact: string | null;
  email?: string | null;
}

export interface Attachment {
  id: string;
  kind: string;
  file_name: string;
  mime: string;
  size_bytes: number;
  sha256: string;
  caption: string | null;
  test_record_id: string | null;
}
