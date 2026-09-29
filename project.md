# NAWI Type-Evaluation Report System (OIML R 76) — Complete Build Guide

> Project: Web portal that records test observations, validates them, calculates permissible errors, decides PASS/FAIL per OIML R 76, and produces standardized type-evaluation reports (PDF + Word) for Non-Automatic Weighing Instruments (NAWIs).
> Problem statement reference: SIH26035 (Department of Consumer Affairs, Legal Metrology).
> Written: 30 Sep 2026.

---

## 0. READ THIS FIRST — how trustworthy each rule in this file is

Legal metrology software must be *correct*, so every rule below carries a tag:

| Tag | Meaning |
|---|---|
| **[V]** | Verified: taken directly from the text of **OIML R 76-1:2006 (E)** (terminology through clause 3.10.4) or **OIML R 76-2:2007 (E)** (all report forms, formulas and checklists), which were fetched while writing this file. |
| **[M]** | From the **NMI P 108 lab procedure manual** (Asia-Pacific Legal Metrology Forum). It is a real lab procedure, **but it was written for the older R 76-1:1992 edition**. Numbers may differ slightly in the 2006 edition. Confirm against Annex A/B of R 76-1:2006. |
| **[C]** | **Confirm**: I could not retrieve this clause text (R 76-1 clauses 4–8 and Annexes A–G were cut off). The value is from general knowledge of the standard. **You must read the clause and confirm before you rely on it.** |

**Do this before writing code:** download these documents (free from oiml.org) and keep them beside you.

1. OIML R 76-1:2006 (E) — https://www.oiml.org/en/files/pdf_r/r076-1-e06.pdf
2. OIML R 76-2:2007 (E) — https://www.oiml.org/en/files/pdf_r/r076-2-e07.pdf
3. NMI P 108 (lab procedure manual) — https://www.industry.gov.au/sites/default/files/2019-05/nmi_p_108.pdf
4. OIML R 60 (load cells) and R 111 (weights) — referenced by R 76.
5. India: Legal Metrology Act 2009, Legal Metrology (General) Rules 2011 and the Legal Metrology (Approval of Models) Rules (check the exact current titles/amendments on the Department of Consumer Affairs website; **[C]**).
6. IEC 60068-2-x and IEC 61000-4-x (only needed to understand the disturbance tests).

**Clauses of R 76-1:2006 you must read in full and cross-check against this file:**
`4.5` (zero devices), `4.6` (tare), `5.1–5.5` (electronic), `Annex A` (A.4.1 to A.6), `Annex B` (B.2, B.3, B.4), `Annex C–F` (modules; only if you support modules), `Annex G` (software).

---

## 1. What you are building (plain words)

A lab engineer logs in, registers the scale being tested, sets the test conditions, and types in the readings from each test (weighing, eccentricity, repeatability, etc.). The software:

1. calculates the error at every point using the OIML formulas,
2. looks up the maximum permissible error (MPE) for that load,
3. decides pass or fail for each test and for the whole instrument,
4. warns about impossible or suspicious numbers,
5. lets a reviewer approve,
6. prints a report in the exact OIML R 76-2 layout as PDF and Word,
7. stores everything so it can be searched later.

### 1.1 Requirements traceability (every line of the problem statement → where it is built)

| Requirement (from problem statement) | Built in section |
|---|---|
| Capture manufacturer, instrument, model, technical parameters | 4 (data model), 13 (forms) |
| Record laboratory and environmental conditions | 4, 8.0 |
| Enter observations for all R 76 tests | 8 (test specs), 13 |
| Auto-calculate permissible errors and compliance | 7 (engine), 8 |
| Validation checks on entered data | 9 |
| Auto pass/fail per OIML R 76 | 7, 8 |
| Standardized digital reports in printable format | 10 |
| PDF + editable (Word) export | 10 |
| Digital repository of completed reports | 11 |
| Secure access, role-based permissions | 5, 14 |
| Support future updates when OIML is revised | 6 (versioned rule sets), 19 |
| Dashboard (completed / in process / history) | 11 |
| Search & retrieval | 11 |
| Attach photographs and supporting documents | 10.5, 4 |
| Digital signatures (optional) | 10.6 |
| Technical documentation (architecture, calculation methodology, deployment) | 18 |

---

## 2. Regulatory background you should be able to explain in the demo

- **Legal Metrology Act, 2009 / General Rules 2011 (India):** instruments used for trade and protection must conform to prescribed standards, get **model (type) approval**, and undergo **verification and stamping** before use. **[C]** (from the problem statement; confirm clause numbers on the DoCA site).
- **OIML R 76-1:2006** gives the metrological and technical requirements and the test methods (Annexes A and B). **[V]**
- **OIML R 76-2:2007** gives the *Type evaluation report* format. Labs are "strongly advised" to use it, and it is mandatory inside the OIML Certificate System / MAA. **[V]**
- The report must be completed page-by-page; some tests (for example weighing performance) are repeated and each repetition goes on its own page; a **multiple-range instrument is tested separately per range with its own general-information form**. **[V]** (R 76-2 introduction)

Your software mirrors R 76-2 because that is the legally recognized format.

---

## 3. Architecture and technology

### 3.1 Recommended stack (chosen so the maths is easy to get right)

| Layer | Choice | Why |
|---|---|---|
| Backend | **Python 3.12 + FastAPI** | Python `decimal` gives exact arithmetic — vital for boundary decisions such as "is 2000.0 e in the 1.0 e band?" |
| Database | **PostgreSQL 16** (SQLite for quick local dev) | JSONB for per-test observations, strong constraints |
| ORM / migrations | SQLAlchemy 2 + Alembic | |
| Frontend | **React + TypeScript + Vite + Tailwind CSS** | Fast forms, live pass/fail readout |
| Forms | React Hook Form + Zod | Client-side validation mirrored on the server |
| Auth | JWT access token (15 min) + refresh token (httpOnly cookie), passwords with **argon2** | |
| PDF | **WeasyPrint** (HTML → PDF) | Same HTML template used for on-screen preview |
| Word | **python-docx** | Editable .docx built from the same report model |
| QR / hash | `qrcode`, `hashlib` (SHA-256) | Certificate verification |
| Digital signature (optional) | **pyHanko** (PDF signing with a .p12 or USB-token DSC) | |
| Files | Local disk in dev, **MinIO/S3** in prod | Photos and documents |
| Tests | pytest + hypothesis (backend), Vitest + Playwright (frontend) | |
| Deploy | Docker Compose + Caddy/nginx | |

> If you prefer Node.js, the public project "nawi-testbench" (GitHub: faizanshahid00007/nawi-testbench) uses Node 20 + SQLite and is a good design reference. **Never use JavaScript `Number` (floating point) for the comparisons** — use a decimal library.

### 3.2 System diagram

```
 Browser (React SPA)
    │  HTTPS / JSON
    ▼
 Reverse proxy (Caddy/nginx) ─── serves built SPA, proxies /api
    │
    ▼
 FastAPI app
   ├─ auth & RBAC middleware
   ├─ routers: users, instruments, applications, evaluations, tests, equipment,
   │           attachments, reports, dashboard, search, admin/rulesets, audit
   ├─ engine/  (PURE functions, no DB access)  ◄── rule set JSON (versioned)
   │     classification.py  mpe.py  error.py  tests/<kind>.py  validate.py
   ├─ reporting/  report_model.py  html_template/  pdf.py  docx.py  qr.py  sign.py
   └─ storage/ (files)  +  PostgreSQL
```

**Golden design rules (copy these; they make the project defensible):**

1. **Engine is a pure function**: `evaluate(instrument, evaluation_context, observations, ruleset) → verdicts`. No database, no clock, no randomness. A report can be recomputed any time and must give the same answer.
2. **Rule set is data, not code** (JSON, versioned). Every constant carries its clause number. A revised OIML edition = a new JSON file. Every report stores the `ruleset_id` and its SHA-256 hash.
3. **Store raw observations immutably.** Store computed values separately and recompute on demand.
4. **Decimal arithmetic everywhere.** Store numbers as strings/NUMERIC, never floats.

### 3.3 Repository layout

```
nawi-portal/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/            config.py security.py deps.py
│  │  ├─ models/          SQLAlchemy models
│  │  ├─ schemas/         Pydantic models
│  │  ├─ routers/         auth.py users.py instruments.py applications.py evaluations.py
│  │  │                   tests.py equipment.py attachments.py reports.py dashboard.py
│  │  │                   search.py rulesets.py audit.py
│  │  ├─ engine/          __init__.py units.py classification.py mpe.py error.py validate.py
│  │  │                   suggest_loads.py evaluate.py
│  │  │                   tests/  weighing.py eccentricity.py repeatability.py discrimination.py
│  │  │                           sensitivity.py tare.py zero.py temperature.py tilting.py
│  │  │                           time_dependence.py stability_eq.py warmup.py voltage.py
│  │  │                           damp_heat.py span_stability.py endurance.py disturbances.py
│  │  │                           checklist.py
│  │  ├─ reporting/       report_model.py templates/report.html.j2 pdf.py docx.py qr.py sign.py
│  │  └─ rulesets/        oiml-r76-2006.json  (+ schema.json)
│  ├─ alembic/
│  ├─ tests/              unit/ golden/ api/
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/ pages/ components/ forms/ api/ hooks/ i18n/
│  └─ package.json
├─ docs/                  architecture.md methodology.md deployment.md user-manual.md
├─ docker-compose.yml
└─ README.md
```

---

## 4. Data model (PostgreSQL)

Keep raw observations in JSONB per test form, but keep identity, workflow and search fields as real columns.

```sql
-- USERS / ROLES -------------------------------------------------------------
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('ADMIN','ENGINEER','REVIEWER','VIEWER')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
  failed_logins INT NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- LABORATORY (who is doing the test) ---------------------------------------
CREATE TABLE laboratories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL, address TEXT, accreditation_no TEXT,   -- e.g. NABL no.
  logo_path TEXT, contact TEXT
);

-- APPLICANT / MANUFACTURER --------------------------------------------------
CREATE TABLE parties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind TEXT CHECK (kind IN ('MANUFACTURER','APPLICANT','AGENT')),
  name TEXT NOT NULL, address TEXT, gstin TEXT, contact TEXT, email TEXT
);

-- INSTRUMENT TYPE / MODEL ("General information concerning the type", R 76-2 p.6) --
CREATE TABLE instruments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_no TEXT,                 -- "Application no."
  type_designation TEXT NOT NULL,      -- "Type designation" (model)
  manufacturer_id UUID REFERENCES parties(id),
  applicant_id UUID REFERENCES parties(id),
  category TEXT,                       -- "Instrument category" (e.g. platform scale, weighbridge, price-computing)
  is_module BOOLEAN NOT NULL DEFAULT FALSE,
  module_error_fraction_pi NUMERIC,    -- "error fraction pi" if module
  accuracy_class TEXT NOT NULL CHECK (accuracy_class IN ('I','II','III','IIII')),
  indication_type TEXT NOT NULL CHECK (indication_type IN ('SELF','SEMI_SELF','NON_SELF')),
  display_kind TEXT CHECK (display_kind IN ('DIGITAL','ANALOG')),
  range_kind TEXT NOT NULL CHECK (range_kind IN ('SINGLE','MULTI_INTERVAL','MULTIPLE_RANGE')),
  min_capacity NUMERIC NOT NULL,       -- Min
  unit TEXT NOT NULL DEFAULT 'kg',     -- kg, g, mg, t, ct
  tare_plus NUMERIC DEFAULT 0,         -- T = +
  tare_minus NUMERIC DEFAULT 0,        -- T = -
  max_safe_load NUMERIC,               -- Lim
  u_nom NUMERIC, u_min NUMERIC, u_max NUMERIC, frequency_hz NUMERIC,
  battery_u_nom NUMERIC,
  power_supply_category TEXT[],        -- MAINS_AC, EXTERNAL_PLUGIN, BATTERY_RECHARGEABLE_CHARGE_IN_USE, BATTERY_OTHER, VEHICLE_12V, VEHICLE_24V
  zero_devices JSONB,                  -- {non_automatic, semi_automatic, automatic, initial, tracking, zero_indicating}
  initial_zero_range_pct NUMERIC,
  zero_setting_range_pct NUMERIC,
  tare_devices JSONB,                  -- {balancing, weighing, preset, subtractive, additive, combined_zero_tare, semi_auto, auto}
  temp_min_c NUMERIC DEFAULT -10, temp_max_c NUMERIC DEFAULT 40,
  temp_range_is_special BOOLEAN DEFAULT FALSE,
  direct_sales_to_public BOOLEAN DEFAULT FALSE,
  level_indicator BOOLEAN, auto_tilt_sensor BOOLEAN, limiting_tilt NUMERIC,
  printer TEXT CHECK (printer IN ('BUILT_IN','CONNECTED','NOT_PRESENT_CONNECTABLE','NO_CONNECTION')),
  software_version TEXT, software_checksum TEXT,
  load_cell JSONB,                     -- {manufacturer,type,capacity,number,classification}
  interfaces JSONB, connected_equipment JSONB,
  submitted_identification_no TEXT,    -- serial no. of sample submitted
  remarks TEXT,
  created_by UUID REFERENCES users(id), created_at TIMESTAMPTZ DEFAULT now()
);

-- one row per weighing range / partial range (R 76-2: e1,Max1,d1,n1 ...) ----
CREATE TABLE instrument_ranges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instrument_id UUID REFERENCES instruments(id) ON DELETE CASCADE,
  idx INT NOT NULL,                    -- 1,2,3
  e NUMERIC NOT NULL, d NUMERIC NOT NULL, max NUMERIC NOT NULL,
  UNIQUE (instrument_id, idx)
);

-- EVALUATION = one test campaign (one "type evaluation report") -------------
CREATE TABLE evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_no TEXT UNIQUE NOT NULL,      -- e.g. LM/NAWI/2026/0001
  instrument_id UUID NOT NULL REFERENCES instruments(id),
  laboratory_id UUID NOT NULL REFERENCES laboratories(id),
  range_index INT,                     -- for MULTIPLE_RANGE: which range this report covers
  ruleset_id TEXT NOT NULL,            -- 'oiml-r76-2006'
  ruleset_sha256 TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK (purpose IN ('TYPE_APPROVAL','VERIFICATION')),
  mpe_context TEXT NOT NULL DEFAULT 'INITIAL' CHECK (mpe_context IN ('INITIAL','IN_SERVICE')),
  status TEXT NOT NULL DEFAULT 'DRAFT'
     CHECK (status IN ('DRAFT','IN_PROGRESS','SUBMITTED','UNDER_REVIEW','RETURNED','APPROVED','ARCHIVED')),
  outcome TEXT CHECK (outcome IN ('PASS','FAIL','INCOMPLETE')),
  evaluation_period_from DATE, evaluation_period_to DATE,
  observer_id UUID REFERENCES users(id),
  resolution_during_test NUMERIC,      -- "smaller than e" (class I etc.)
  auto_zero_status TEXT CHECK (auto_zero_status IN ('NON_EXISTENT','NOT_IN_OPERATION','OUT_OF_WORKING_RANGE','IN_OPERATION')),
  initial_zero_gt_20pct BOOLEAN,
  created_by UUID REFERENCES users(id), created_at TIMESTAMPTZ DEFAULT now(),
  submitted_at TIMESTAMPTZ, approved_by UUID REFERENCES users(id), approved_at TIMESTAMPTZ,
  approval_hash TEXT                   -- SHA-256 over canonical JSON of all observations + verdicts
);

-- TEST EQUIPMENT (R 76-2 p.8) ----------------------------------------------
CREATE TABLE equipment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind TEXT CHECK (kind IN ('WEIGHT_SET','THERMOMETER','HYGROMETER','BAROMETER','CHAMBER','ESD_GUN','BURST_GEN','SURGE_GEN','EM_FIELD','RF_CONDUCTED','VOLTAGE_SOURCE','TIMER','OTHER')),
  name TEXT, model TEXT, serial_no TEXT,
  accuracy_class_or_uncertainty TEXT,       -- e.g. 'F1', 'M1', 'U=0.5 mg'
  cert_no TEXT, calibrated_on DATE, valid_until DATE,
  weight_nominal NUMERIC, weight_error NUMERIC, weight_uncertainty NUMERIC  -- for weights (used in the 1/3 mpe check)
);
CREATE TABLE evaluation_equipment (
  evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
  equipment_id UUID REFERENCES equipment(id),
  PRIMARY KEY (evaluation_id, equipment_id)
);

-- ENVIRONMENT (at start / at max load / at end) — attached to each test record ---
-- stored inside test_records.environment JSONB:
--   { "start":{"temp":20.5,"rh":45,"time":"10:05","pressure":1003.1},
--     "max":{...}, "end":{...} }

-- TEST RECORDS: one row per *page* of R 76-2 --------------------------------
CREATE TABLE test_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,        -- see section 8: WEIGHING, TEMP_NOLOAD, ECC_WEIGHTS, ECC_ROLLING, DISC_DIGITAL, ...
  form_no TEXT,              -- R 76-2 numbering '1','2','3.1', ... '12.4a'
  instance_no INT NOT NULL DEFAULT 1,   -- repeat pages (e.g. weighing test at 5 temperatures)
  condition_label TEXT,      -- e.g. 'Initial 20 C', 'High 40 C', 'Damp heat b)'
  test_date DATE, observer_id UUID REFERENCES users(id),
  environment JSONB,
  observations JSONB NOT NULL,          -- RAW entries (immutable after SUBMITTED)
  computed JSONB,                       -- engine output cache (recomputable)
  verdict TEXT CHECK (verdict IN ('PASSED','FAILED','NOT_APPLICABLE','PENDING')),
  warnings JSONB,                       -- plausibility warnings carried into the report
  remarks TEXT,
  created_by UUID REFERENCES users(id), updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (evaluation_id, kind, instance_no)
);

-- CHECKLIST (R 76-2 test 17) -------------------------------------------------
CREATE TABLE checklist_results (
  evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
  item_code TEXT,                      -- e.g. '7.1.1', '4.5.2', '5.5.1'
  state TEXT CHECK (state IN ('PASSED','FAILED','NOT_APPLICABLE')),
  device_state TEXT CHECK (device_state IN ('EXISTENT','NON_EXISTENT')),
  remarks TEXT,
  PRIMARY KEY (evaluation_id, item_code)
);

-- ATTACHMENTS ---------------------------------------------------------------
CREATE TABLE attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
  test_record_id UUID REFERENCES test_records(id),
  kind TEXT CHECK (kind IN ('PHOTO','SKETCH','DOCUMENT','CERTIFICATE','RAW_DATA')),
  file_name TEXT, mime TEXT, size_bytes BIGINT, sha256 TEXT, storage_path TEXT,
  caption TEXT, include_in_report BOOLEAN DEFAULT TRUE,
  uploaded_by UUID REFERENCES users(id), uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- REVIEW / SIGNATURE / EXPORTS ---------------------------------------------
CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
  reviewer_id UUID REFERENCES users(id),
  decision TEXT CHECK (decision IN ('RETURNED','APPROVED')),
  comment TEXT, decided_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE report_exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
  format TEXT CHECK (format IN ('PDF','DOCX','JSON')),
  version INT, storage_path TEXT, sha256 TEXT,
  signed BOOLEAN DEFAULT FALSE, created_by UUID, created_at TIMESTAMPTZ DEFAULT now()
);

-- RULE SETS & AUDIT ---------------------------------------------------------
CREATE TABLE rulesets (
  id TEXT PRIMARY KEY,                 -- 'oiml-r76-2006'
  title TEXT, effective_from DATE, sha256 TEXT NOT NULL, document JSONB NOT NULL,
  is_active BOOLEAN DEFAULT TRUE
);
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  at TIMESTAMPTZ DEFAULT now(), user_id UUID, action TEXT, entity TEXT, entity_id TEXT,
  before JSONB, after JSONB, ip INET
);
CREATE INDEX ON evaluations (status, outcome);
CREATE INDEX ON instruments (type_designation);
CREATE INDEX ON test_records (evaluation_id, kind);
```

Rules for the data layer:

- After an evaluation is `SUBMITTED`, `observations` become read-only (enforce in service layer and with a DB trigger). To correct, a reviewer sets `RETURNED`.
- Instrument particulars freeze once used in an `APPROVED` report; create a new instrument revision instead of editing.
- Every write to a test record inserts an `audit_log` row.

---

## 5. Roles, permissions and workflow

### 5.1 Roles

| Action | ADMIN | ENGINEER | REVIEWER | VIEWER |
|---|:-:|:-:|:-:|:-:|
| Manage users, labs, rule sets, equipment master | ✔ | – | – | – |
| Create/edit instruments & evaluations | ✔ | ✔ | – | – |
| Enter/modify observations (before submit) | – | ✔ (own or assigned) | – | – |
| Upload attachments | ✔ | ✔ | ✔ | – |
| Submit for review | – | ✔ | – | – |
| Return / approve / sign | – | – | ✔ | – |
| View reports and dashboard | ✔ | ✔ | ✔ | ✔ |
| Export PDF/Word | ✔ | ✔ | ✔ | ✔ (approved only) |
| View audit log | ✔ | – | ✔ | – |

Separation of duties: the **approver cannot be the same person as the observer**.

### 5.2 Workflow state machine

```
DRAFT ──(first observation saved)──► IN_PROGRESS
IN_PROGRESS ──(engineer submits; all required tests present)──► SUBMITTED
SUBMITTED ──(reviewer opens)──► UNDER_REVIEW
UNDER_REVIEW ──(returns with comment)──► RETURNED ──(engineer fixes)──► IN_PROGRESS
UNDER_REVIEW ──(approves + signs)──► APPROVED ──(archive after retention rule)──► ARCHIVED
```

Submission gate (server-side): every test that the rule set marks *required for this purpose and this instrument* has a verdict of `PASSED`, `FAILED` or `NOT_APPLICABLE`; no unresolved **error**-level validation; test equipment recorded; at least the general-information page complete. `outcome` = `FAIL` if any required test failed, `INCOMPLETE` if any required test is pending, else `PASS`.

---

## 6. The rule set (all constants and tables, ready to paste into JSON)

Save as `backend/app/rulesets/oiml-r76-2006.json`. Numbers are strings so they load as `Decimal`. Every entry has a `clause`.

### 6.1 Accuracy classes — R 76-1 Table 1 and Table 3 **[V]**

| Class | Name | Symbol on instrument |
|---|---|---|
| I | Special | I (inside an oval; **never a circle**, because a circle means constant relative error, R 34) |
| II | High | II |
| III | Medium | III |
| IIII | Ordinary | IIII |

**Table 3 — classification [V]** (n = Max / e)

| Class | Verification scale interval e | n minimum | n maximum | Min (lower limit of capacity) |
|---|---|---|---|---|
| I | 0.001 g ≤ e | 50 000 (exception: class I with d < 0.1 mg may have less, 3.4.4) | – | 100 e |
| II | 0.001 g ≤ e ≤ 0.05 g | 100 | 100 000 | 20 e |
| II | 0.1 g ≤ e | 5 000 | 100 000 | 50 e |
| III | 0.1 g ≤ e ≤ 2 g | 100 | 10 000 | 20 e |
| III | 5 g ≤ e | 500 | 10 000 | 20 e |
| IIII | 5 g ≤ e | 100 | 1 000 | 10 e |

Notes **[V]**: it is normally not feasible to test/verify an instrument with e < 1 mg (weights' uncertainty). Min is reduced to **5 e for grading instruments** (postal scales, waste weighers). For instruments with an auxiliary indicating device Min uses **d** instead of e (3.4.3).

### 6.2 Verification scale interval rules **[V]**

- Graduated instrument, no auxiliary indicating device: **e = d** (Table 2).
- With an auxiliary indicating device (classes I and II only; **not allowed on multi-interval**; only to the right of the decimal sign): **d < e ≤ 10 d** and **e = 10^k kg** (k integer, may be negative/zero). Exception class I with d < 1 mg: e = 1 mg. (3.4.1, 3.4.2)
- Form of scale interval for indication: **(1, 2 or 5) × 10^k** (checklist 4.2.2.1). **[V]**

### 6.3 MPE bands — R 76-1 Table 6 (initial verification) **[V]**

Load *m* is expressed **in verification scale intervals e** (of the range the load is in). Absolute value of MPE:

| MPE | Class I | Class II | Class III | Class IIII |
|---|---|---|---|---|
| ± 0.5 e | 0 ≤ m ≤ 50 000 | 0 ≤ m ≤ 5 000 | 0 ≤ m ≤ 500 | 0 ≤ m ≤ 50 |
| ± 1.0 e | 50 000 < m ≤ 200 000 | 5 000 < m ≤ 20 000 | 500 < m ≤ 2 000 | 50 < m ≤ 200 |
| ± 1.5 e | 200 000 < m | 20 000 < m ≤ 100 000 | 2 000 < m ≤ 10 000 | 200 < m ≤ 1 000 |

- **In service: MPE = 2 × the value above** (3.5.2). **[V]**
- Applies to gross loads; with a tare device in operation it applies to **net loads**, for every possible tare value except preset tare (3.5.3.3). MPE for a tare-weighing device = the instrument's MPE at the same load (3.5.3.4). **[V]**

```json
"mpe_bands": {
  "I":    [{"up_to":"50000","mult":"0.5"},{"up_to":"200000","mult":"1.0"},{"up_to":null,"mult":"1.5"}],
  "II":   [{"up_to":"5000","mult":"0.5"},{"up_to":"20000","mult":"1.0"},{"up_to":"100000","mult":"1.5"}],
  "III":  [{"up_to":"500","mult":"0.5"},{"up_to":"2000","mult":"1.0"},{"up_to":"10000","mult":"1.5"}],
  "IIII": [{"up_to":"50","mult":"0.5"},{"up_to":"200","mult":"1.0"},{"up_to":"1000","mult":"1.5"}]
},
"in_service_multiplier": "2"
```

### 6.4 Multi-interval instruments **[V]** (3.3)

- Partial range i has e_i (e_{i+1} > e_i), Max_i, and **Min_i = Max_{i-1}** (Min_1 = Min).
- n_i = Max_i / e_i.
- e_i, n_i and Min_1 must satisfy Table 3 for the class.
- Except for the last partial range: **Max_i / e_{i+1} ≥ 50 000 (I), 5 000 (II), 500 (III), 50 (IIII)** (Table 4).
- MPE at load m: find the partial range containing m; compute m / e_i; look up Table 6 with that number; MPE = multiplier × e_i.
- Near zero, e = e_1. With tare, the ranges apply to the net load.

**Worked example from the standard (use as a golden test) [V]:** class III, e = 1 / 2 / 10 g, Max = 2 / 5 / 15 kg, Min = 20 g.
Partial ranges: (20 g, 2 kg, e1=1 g, n1=2000); (2 kg, 5 kg, e2=2 g, n2=2500); (5 kg, 15 kg, e3=10 g, n3=1500). Expected MPE:

| Load m | MPE |
|---|---|
| 0 – 500 g | ±0.5 g |
| > 500 – 2000 g | ±1 g |
| > 2000 – 4000 g | ±2 g |
| > 4000 – 5000 g | ±3 g |
| > 5000 – 15000 g | ±10 g |

### 6.5 Other constants

```json
"constants": {
  "weights_error_max_fraction_of_mpe": {"value":"1/3","clause":"3.7.1"},
  "auxiliary_verification_device_mpe_fraction": {"value":"1/3","clause":"3.7.2"},
  "auxiliary_weights_effect_fraction": {"value":"1/5","clause":"3.7.2"},
  "substitution_repeatability": [
      {"repeatability_le_e":"0.3","min_std_weight_fraction_of_Max":"1/3"},
      {"repeatability_le_e":"0.2","min_std_weight_fraction_of_Max":"1/5"}
  ],
  "substitution_default_fraction_of_Max": "1/2",
  "rounding_elimination_if_d_gt": {"value":"0.2","unit":"e","clause":"3.5.3.2"},
  "default_temperature_limits_c": {"min":"-10","max":"40","clause":"3.9.2.1"},
  "special_temperature_min_span_c": {"I":"5","II":"15","III":"30","IIII":"30","clause":"3.9.2.2"},
  "temp_no_load_zero_change_limit_e": {"per_c_class_I":"1","per_c_other":"5","limit":"1 e","clause":"3.9.2.3"},
  "tilt_default_limit": {"value":"50/1000","clause":"3.9.1.1 c"},
  "tilt_no_load_limit_e": {"value":"2","exclude_class":"II (unless direct sales to public)","clause":"3.9.1.1"},
  "creep": {"within_30min_e":"0.5","between_15_and_30min_e":"0.2","fallback_4h":"|mpe|","clause":"3.9.4.1"},
  "zero_return": {"limit_e":"0.5","multi_interval_uses":"e1","multiple_range_5min_e":"e1","clause":"3.9.4.2"},
  "durability_endurance_applies_if_Max_le": {"value":"100 kg","limit":"|mpe|","clause":"3.9.4.3"},
  "module_apportioning": {"sum_squares_le":"1","digital_only_p":"0","weighing_module_p":"1","other_p_range":["0.3","0.8"],"mechanical_default_p":"0.5","clause":"3.10.2.1"},
  "zero_accuracy_e": {"value":"0.25","clause":"4.5.2 / 4.6.3 (checklist)"},
  "zero_tracking_rate_max_d_per_s": {"value":"0.5","clause":"4.5.7 (checklist)"},
  "digital_display_overrange": {"value":"Max + 9 e","clause":"4.2.3 (checklist)"},
  "negative_indication_limit_d": {"value":"20","clause":"4.2.3 (checklist)"}
}
```

Table 7 — module error fractions p_i **[V]** (3.10.2.1):

| Performance criterion | Load cell | Electronic indicator | Connecting elements etc. |
|---|---|---|---|
| Combined effect | 0.7 | 0.5 | 0.5 |
| Temperature effect on no-load indication | 0.7 | 0.5 | 0.5 |
| Power supply variation | – | 1 | – |
| Effect of creep | 1 | – | – |
| Damp heat | 0.7 | 0.5 | 0.5 |
| Span stability | – | 1 | – |

### 6.6 Power-supply voltage limits — 3.9.3 **[V]**

| Supply category | Lower limit | Upper limit |
|---|---|---|
| Public mains (AC) | 0.85 × U_nom (or 0.85 × U_min) | 1.10 × U_nom (or 1.10 × U_max) |
| External/plug-in supply (AC or DC), incl. rechargeable battery that can be charged during operation | minimum operating voltage | 1.20 × U_nom (or 1.20 × U_max) |
| Non-rechargeable battery (DC), incl. rechargeable if charging during operation is not possible | minimum operating voltage | U_nom (or U_max) |
| 12 V road-vehicle battery | minimum operating voltage | 16 V |
| 24 V road-vehicle battery | minimum operating voltage | 32 V |

"Minimum operating voltage" = lowest voltage before the instrument switches itself off. Below the manufacturer's stated value the instrument must either work correctly or show no weight value. If a voltage range (U_min/U_max) is marked, use the **average** as the reference value (R 76-2 form 11). **[V]**

### 6.7 Humidity limit during temperature tests **[M]**

Absolute humidity must not exceed **20 g/m³** during the temperature tests. Use the Magnus formula instead of a lookup table:

```
es(T)  = 6.112 * exp(17.62*T / (243.12 + T))        # hPa, T in °C
AH     = es(T) * RH * 2.1674 / (273.15 + T)          # g/m³, RH in %
warn if AH > 20
```
Check: at 33 °C the manual's table gives max RH 57 % → this formula gives 20.2 g/m³ ✓.

### 6.8 Test catalogue (rule-set entries) **[V]** (R 76-2 contents)

Each entry: `kind`, `form_no`, `clause`, `applies_to`, `required_for`.

| form_no | kind | R 76-1 clause | Applies when | Required for type approval |
|---|---|---|---|---|
| 1 | WEIGHING (performance) | A.4.4, A.5.3.1 | always (repeated for each condition) | Yes |
| 2 | TEMP_NOLOAD | A.5.3.2 | always | Yes |
| 3.1 | ECC_WEIGHTS | A.4.7.1-3 | always (unless rolling load only) | Yes |
| 3.2 | ECC_ROLLING | A.4.7.4 | vehicle/rolling load instruments | If applicable |
| 4.1.1 | DISC_DIGITAL | A.4.8.2 | digital; **only d ≥ 5 mg** (3.8.2.2) | If applicable |
| 4.1.2 | DISC_ANALOG | A.4.8.1 | analog self-indicating | If applicable |
| 4.1.3 | DISC_NONSELF | A.4.8.1 | non-self-indicating | If applicable |
| 4.2 | SENSITIVITY | A.4.9 | non-self-indicating | If applicable |
| 5 | REPEATABILITY | A.4.10 | always | Yes |
| 6.1 | ZERO_RETURN | A.4.11.2 | classes II, III, IIII | Yes |
| 6.2 | CREEP | A.4.11.1 | classes II, III, IIII | Yes |
| 7 | STABILITY_EQ | A.4.12 | printing/storage/zero-setting/tare-balancing present | If applicable |
| 8 | TILTING | A.5.1 | class II/III/IIII liable to be tilted (3.9.1.1); class I: level device required but not tested | If applicable |
| 9 | TARE | A.4.6.1 | tare device present | If applicable |
| 10 | WARMUP | A.5.2 | electronic | Yes (electronic) |
| 11 | VOLTAGE | A.5.4 | electronic | Yes (electronic) |
| 12.1 | DIST_DIPS | B.3.1 | electronic, AC mains | Yes (electronic) |
| 12.2a/b | DIST_BURST_MAINS / DIST_BURST_IO | B.3.2 | electronic | Yes |
| 12.3a/b | DIST_SURGE_AC / DIST_SURGE_OTHER | B.3.3 | electronic | Yes |
| 12.4a/b | DIST_ESD_DIRECT / DIST_ESD_INDIRECT | B.3.4 | electronic | Yes |
| 12.5 | DIST_RADIATED | B.3.5 | electronic | Yes |
| 12.6 | DIST_CONDUCTED_RF | B.3.6 | electronic with mains/I-O ports | Yes |
| 12.7a/b | DIST_VEHICLE_SUPPLY / DIST_VEHICLE_COUPLING | B.3.7 | powered from road-vehicle supply | If applicable |
| 13a/b/c | DAMP_HEAT_INITIAL / _HIGH / _FINAL | B.2 | electronic | Yes (electronic) |
| 14 | SPAN_STABILITY | B.4 | electronic | Yes (electronic) |
| 15 | ENDURANCE | A.6 | Max ≤ 100 kg; **always performed last** | If applicable |
| 16 | CONSTRUCTION | – | always | Yes (free text + photo) |
| 17 | CHECKLIST | – | always (17.1–17.4 subsets) | Yes |

Order rule **[V]** (3.10.1): the endurance test (A.6) is performed **after all the other tests in Annexes A and B**. Enforce this: block entry of form 15 "final test" until other tests are saved (warning, not hard-stop).

Applicability flags to compute from the instrument: `is_electronic`, `is_digital`, `class`, `Max`, `d`, `has_printer_or_storage`, `has_tare`, `has_zero_tracking`, `direct_sales`, `vehicle_powered`, `liable_to_tilt`, `is_non_self_indicating` (non-self-indicating instruments follow clause 6 of R 76-1 instead of the 17.1 checklist **[V]**).

---

## 7. Calculation engine — symbols, formulas, code

### 7.1 Symbols **[V]** (R 76-2 explanatory notes)

| Symbol | Meaning |
|---|---|
| I, In | Indication, nth indication |
| L | Load (true value of the applied mass) |
| ΔL | Additional load needed to reach the next changeover point |
| P | Indication prior to rounding (digital) |
| E | Error |
| E0 | Error at or near zero |
| Ec | Corrected error |
| mpe | Maximum permissible error (absolute value) |
| e, d | Verification scale interval, actual scale interval |
| n | Number of verification intervals = Max / e |
| EUT | Equipment under test |

### 7.2 Core formulas **[V]**

```
P   = I + ½·r − ΔL              # r = indication step used during the test (r = d normally; R 76-2 prints "½ e" because d = e)
E   = P − L   = I + ½·r − ΔL − L
Ec  = E − E0                      # E0 = error calculated at or near zero
pass ⇔ |Ec| ≤ |mpe(L)|
```

- **The changeover-point method.** At a load L the indication is I. Add small weights (e.g. 0.1 e each) one at a time until the indication jumps by one step (I + r). The total added is ΔL. This removes rounding error. **[V/M]**
- It must be used when d > 0.2 e (rounding error must be eliminated, 3.5.3.2). **[V]** If d ≤ 0.2 e the rounding error is small and the engine may accept "direct reading" mode: P = I, ΔL not required (flag `method = "direct"`). **[C]**
- **E0 (error at zero):**
  - Non-automatic zero: E0 = ½ r − ΔL0 (I0 = 0, L0 = 0). **[M]**
  - Automatic zero-setting / zero-tracking **in operation**: put 10 e on the receptor to take the instrument out of working range, then E0 = I0 + ½ r − ΔL0 − L0. **[M]**
- If the initial zero-setting range is > 20 % of Max, a **supplementary test** at the upper limit of that range is required (A.4.4.2; standard procedure #6). **[M]**
- Zero-setting accuracy and tare-setting accuracy: **|E0| ≤ 0.25 e**. **[V]** (checklist 4.5.2 / 4.6.3; form 7)

### 7.3 Python skeleton (copy and extend)

```python
# app/engine/units.py
from decimal import Decimal as D, getcontext
getcontext().prec = 34

def dec(x) -> D:
    """Always build Decimals from strings, never from floats."""
    return x if isinstance(x, D) else D(str(x))
```

```python
# app/engine/classification.py
from dataclasses import dataclass
from decimal import Decimal as D
from .units import dec

@dataclass(frozen=True)
class Range:
    idx: int      # 1,2,3
    e: D
    d: D
    max: D
    min: D        # lower bound of this partial range (Max_{i-1}, or instrument Min for idx 1)

@dataclass(frozen=True)
class Instrument:
    cls: str                      # 'I','II','III','IIII'
    ranges: tuple[Range, ...]     # single-range => one element
    min_cap: D
    tare_plus: D = D(0)

    @property
    def max(self) -> D: return self.ranges[-1].max

    def range_for_load(self, load: D) -> Range:
        load = dec(load)
        for r in self.ranges:
            if load <= r.max:
                return r
        raise ValueError("Load exceeds Max")     # validation layer turns this into a message
```

```python
# app/engine/mpe.py
from decimal import Decimal as D
from .units import dec

def band_multiplier(rs: dict, cls: str, m_in_e: D) -> D:
    for b in rs["mpe_bands"][cls]:
        if b["up_to"] is None or m_in_e <= D(b["up_to"]):
            return D(b["mult"])
    raise ValueError("Load beyond the highest band of Table 6 for this class")

def mpe(rs: dict, inst, load, context: str = "INITIAL") -> D:
    """Absolute MPE for a (gross or net) load, following 3.3 and 3.5.1/3.5.2."""
    load = dec(load)
    r = inst.range_for_load(load)             # multi-interval: partial range that contains the load
    mult = band_multiplier(rs, inst.cls, load / r.e)
    value = mult * r.e
    if context == "IN_SERVICE":
        value *= D(rs["in_service_multiplier"])
    return value
```

```python
# app/engine/error.py
from decimal import Decimal as D
from .units import dec

def point_error(I, L, dL, step, method="changeover"):
    """Returns (P, E). step = indication step used in the test (d)."""
    I, L, dL, step = map(dec, (I, L, dL, step))
    P = I if method == "direct" else I + step / 2 - dL
    return P, P - L

def corrected(E, E0):
    return dec(E) - dec(E0)
```

```python
# app/engine/tests/weighing.py   (forms 1, 9, 13a-c, 15a/c share this)
def evaluate_weighing(rs, inst, ctx, obs):
    """
    obs = {
      "zero": {"L": "0.02", "I": "0.020", "dL": "1.0"},          # near-zero row (marked * in the form)
      "points": [ {"L": "0.04", "up": {"I": "0.040", "dL": "1.2"}, "down": {"I": "0.040", "dL": "1.2"}}, ... ]
    }
    """
    step = ctx.resolution or inst.ranges[0].d
    _, E0 = point_error(obs["zero"]["I"], obs["zero"]["L"], obs["zero"]["dL"], step)
    rows, ok = [], True
    for p in obs["points"]:
        L = dec(p["L"]); m = mpe(rs, inst, L, ctx.mpe_context)
        row = {"L": L, "mpe": m}
        for dirn in ("up", "down"):
            if p.get(dirn) and p[dirn].get("I") not in (None, ""):
                r = inst.range_for_load(L)
                P, E = point_error(p[dirn]["I"], L, p[dirn]["dL"], ctx.resolution or r.d)
                Ec = E - E0
                row[dirn] = {"E": E, "Ec": Ec, "pass": abs(Ec) <= m}
                ok &= row[dirn]["pass"]
        rows.append(row)
    return {"E0": E0, "rows": rows, "verdict": "PASSED" if ok else "FAILED"}
```

### 7.4 Automatic test-load suggestion (saves the engineer time and prevents bad loads)

Generate the load list for the weighing test **[M]** (standard procedure #4 and initial intrinsic error A.4.4):

1. At least **5** test loads (other tests) — and at least **10** for the initial intrinsic error test **[M/C]**.
2. Loads span from **Min to Max**.
3. Include **the loads at MPE change points**: for class III = 500 e and 2000 e (and 10 000 e is the upper limit), class II = 5000 e, 20 000 e, class I = 50 000 e, 200 000 e, class IIII = 50 e, 200 e. For multi-interval include all MPE change points in every partial range.
4. **Do not use a load exactly at the point where the scale interval changes**; use a load about **5 e below** it.
5. **Do not use Max if over-range blanking occurs at Max**; use about **Max − 5 e**.
6. Tests run **increasing** from minimum to maximum, then **decreasing** back to zero (↑ and ↓ columns in the forms).
7. Weights must have error ≤ 1/3 of the MPE at that load (3.7.1). The engine checks this against equipment records.

```python
def suggest_loads(rs, inst, n_min=10, blanking_at_max=False):
    e_last = inst.ranges[-1].e
    loads = {inst.min_cap}
    for r in inst.ranges:
        for b in rs["mpe_bands"][inst.cls]:
            if b["up_to"]:
                x = D(b["up_to"]) * r.e
                if r.min < x <= r.max: loads.add(x)          # MPE change point inside this range
        if r.idx < len(inst.ranges):
            loads.add(r.max - 5 * r.e)                       # stay 5 e below a scale-interval change
    loads.add(inst.max - (5 * e_last if blanking_at_max else 0))
    # fill up with evenly spaced loads until n_min reached
    ...
    return sorted(loads)
```

### 7.5 Overall verdict logic

```
test verdict     = PASSED  if every criterion of that test passes
                 = FAILED  if any criterion fails
                 = NOT_APPLICABLE if rule-set applicability says so
                 = PENDING if required data is missing
report outcome   = FAIL if any required test FAILED
                 = INCOMPLETE if any required test PENDING
                 = PASS otherwise
```
In the disturbance tests (12.x) a fault > e is **acceptable if it is detected and acted upon, or if it is not a "significant fault" by definition** (T.5.5.6) — the engineer must enter an explanation in the "Yes (remarks)" column. **[V]**
Significant fault **[V]** (T.5.5.6): a fault greater than e (for multi-interval, the e of the partial range). **Not** significant even if > e: faults from simultaneous and mutually independent causes; faults making measurement impossible; faults so serious they are obvious to everyone; transitory faults (momentary indication variations that cannot be interpreted, memorized or transmitted as a result).

---

## 8. Test-by-test specification

For each test: **inputs → formulas → pass rule → validations → form**. Environmental block (all tests): temperature, relative humidity, time at *start / at max load / at end*; barometric pressure **only for class I** (and where IEC test provisions require it, and for span stability). **[V]** ("Bar. pres." rule in R 76-2 notes)

Common header fields on every test page **[V]**: Application no., Type designation, Date, Observer, Verification scale interval e, Resolution during test (smaller than e), state of automatic zero-setting/tracking device: `Non-existent | Not in operation | Out of working range | In operation`, and page numbering `Report page ../..`.

### 8.0 General preparation (before any test) **[M]**

1. Record general info (R 76-2 pp. 6-8) incl. test equipment traceability.
2. Instrument on firm table, levelled; power on; **warm up ≥ 30 min**.
3. **Pre-load**: apply Max in practical steps, remove, re-zero (standard procedure #3, A.4.1.10).
4. Check that the error at Max is within MPE before continuing; if not, the applicant must recalibrate.
5. Determine automatic zero status with 20 × 0.1 d weights at 2 s intervals: if after 20 the display still shows zero → device *in operation*; otherwise *non-existent / not in operation*.
6. Weights class guidance: F1 for class II, F1–M1 for III, F2–M3 for IIII, E1/E2 for class I. **[M]** (verify against R 111).
7. Temperature/humidity/pressure instruments must be calibrated and traceable and listed in test equipment.

### 8.1 Form 1 — Weighing performance (A.4.4, A.5.3.1) **[V form; M procedure]**

- **Inputs:** zero row (near-zero, marked *), then for each load L: indication I and additional load ΔL, going ↑ (increasing) and ↓ (decreasing).
- **Formulas:** `E = I + ½e − ΔL − L`, `Ec = E − E0`.
- **Pass:** `|Ec| ≤ |mpe|` at every load, both directions.
- **Extras:** flag `initial_zero_gt_20pct`; if true, engine requires a second weighing page (supplementary test) with the load equal to the positive limit of the initial zero range, after power off/on.
- **Repeat pages:** initial (20 °C), high temperature, low temperature, 5 °C (see 8.3), final 20 °C; and after damp heat (form 13). Each page is a separate `test_records` row (`instance_no`, `condition_label`).
- **Validations:** L ≤ Max + T+; L not equal to a scale-interval change point (warn); I within ±(1 + 10)·e of L (warn, likely typo); ΔL between 0 and step (warn if outside, because ΔL is the extra needed to change by one step); ≥ 5 loads (≥ 10 for the initial intrinsic error page) covering Min…Max and MPE change points (warn if missing).

### 8.2 Form 2 — Temperature effect on no-load indication (A.5.3.2)

- **Inputs per temperature:** date, time, temperature, zero indication I, ΔL (measured with 20 e on the receptor when zero-tracking/auto-zero is in operation).
- **Formulas:** `P = I + ½e − ΔL`; `ΔP = P₂ − P₁` between consecutive tests at different temperatures; `ΔT = T₂ − T₁`; `zero change per 5 °C = |ΔP| / |ΔT| × 5` (class I: `× 1`). **[V/M]**
- **Pass:** zero change per 5 °C **< e** (classes II, III, IIII); per 1 °C **< e** (class I). For multi-interval/multiple range use the **smallest** e. (3.9.2.3 **[V]**)
- **Golden example [M]:** P(20.1 °C)=20.0 g, P(40.3 °C)=22.6 g → ΔP=2.6 g, ΔT=20.2 → 0.6436 g per 5 °C.
- **Also record** the report page number of the weighing test done together with each temperature step (form column "Report page"). **[V]**

### 8.3 Static temperature sequence (A.5.3.1 combined with A.5.3.2) **[M] — confirm against Figure 11 of R 76-1:2006**

For limits −10 °C / +40 °C: reference 20 °C → 40 °C → −10 °C → 5 °C → 20 °C. At each: stabilise (chamber temperature stable ≥ 30 min and zero reading constant), **wait 2 h**, log zero (with 20 e), pre-load, weighing test, **recover ~1 h**, log zero again. Instrument powered ≥ 5 h before first test. Temperature ranges: default −10/+40; if special limits are marked, the span must be at least 5 °C (I), 15 °C (II), 30 °C (III, IIII) **[V]**; validation rule V-INS-012.
Let the app generate the temperature schedule from `temp_min_c`/`temp_max_c` (reference 20 °C, high, low, +5 °C only when the low limit ≤ 0 °C **[C]**, 20 °C) and create the weighing pages automatically.

### 8.4 Form 3 — Eccentricity (A.4.7)

Test load and location count depend on the load receptor **[V]** (3.6.2):

| Case | Test load per position | Clause |
|---|---|---|
| ≤ 4 points of support (default) | **1/3 × (Max + T₊)** | 3.6.2.1 |
| n > 4 points of support | **1/(n − 1) × (Max + T₊)** on each point of support | 3.6.2.2 |
| Tank / hopper (minimal off-centre) | **1/10 × (Max + T₊)** on each point of support | 3.6.2.3 |
| Rolling loads (vehicle/rail) | the usual heaviest, most concentrated rolling load, **≤ 0.8 × (Max + T₊)**, at different points | 3.6.2.4 |

- **Inputs:** sketch (upload or draw), location number, load, I, ΔL for each location; zero row before each measurement ("determined prior to each measurement").
- **Formulas:** as in 7.2. **Pass:** `|Ec| ≤ |mpe(L)|` at each location. **[V]**
- Rolling form 3.2 also records: number of sections of the divided load receptor, direction (← / →), location.
- Mobile instruments: record if A.4.7.5 applied. **[V]**
- 4-quadrant default locations: centre + 4 quarters (numbered 1-5 as in the manual). **[M]**

### 8.5 Form 4 — Discrimination and sensitivity (A.4.8, A.4.9)

Loads: Min, 1/2 Max, Max. Never use the over-range blanking point as a change point; use Max − 5 e. **[M]**

| Sub-form | Applies | Method | Pass rule |
|---|---|---|---|
| 4.1.1 Digital | digital, **d ≥ 5 mg** **[V]** | At load L record I₁. Remove small weights until the indication drops one step, then add 0.1 d, then apply an extra load of **1.4 d**. Record I₂. | `I₂ − I₁ ≥ d` (indication changes unambiguously) |
| 4.1.2 Analog | analog self-indicating | Extra load = |mpe| (≥ 1 mg) gently placed | `I₂ − I₁ ≥ 0.7 × |mpe|` (permanent displacement ≥ 0.7 × extra load) |
| 4.1.3 Non-self-indicating | clause 6 instruments | Extra load = **0.4 × |mpe|** (≥ 1 mg) | Visible displacement of indicating element ("+" marks) |
| 4.2 Sensitivity | non-self-indicating | Extra load = |mpe| applied while oscillating | Permanent displacement ≥ **1 mm** (class I, II); **2 mm** (class III/IIII, Max ≤ 30 kg); **5 mm** (class III/IIII, Max > 30 kg) |

### 8.6 Form 5 — Repeatability (A.4.10)

- **Loads:** about **50 % of Max** and **Max (or near Max)** (Max − 5 e if blanking). For multi-interval, the first load should be near Max of the lowest partial range. **[M]**
- **Number of weighings:** **10** per load; **3** per load if Max > 1000 kg. **[M]** (verify A.4.10)
- **Formulas:** `P = I + ½e − ΔL`, `E = P − L`; range `Pmax − Pmin` (equivalently Emax − Emin).
- **Pass (both):** a) `|E| ≤ |mpe|` for every weighing (3.6); b) `Emax − Emin ≤ |mpe|` (3.6.1). **[V]**
- Note whether the indication returns to zero between weighings; re-zero if not. Record auto-zero status (`Non-existent | In operation`).
- **Golden example [M]:** e=5 g, load 7.5 kg: ΔL values 2.5/3.0 g → P = 7.5000 or 7.4995 kg; Pmax−Pmin = 0.5 g, mpe = 5 g → PASS. Load 15 kg: ΔL 3.0/3.5 g → Pmax−Pmin = 0.5 g, mpe 7.5 g → PASS.
- **Substituted test loads at verification (3.7.3) [V]:** standard weights ≥ 1/2 Max; may be reduced to 1/3 Max if repeatability error ≤ 0.3 e; to 1/5 Max if ≤ 0.2 e (repeatability measured with 3 placements of the substitute load).

### 8.7 Form 6.1 — Zero return (A.4.11.2)

- Zero reading P₀ (before loading). Load for 30 min (Max or near Max). Remove load, read zero P₃₀ (as soon as stabilised).
- **Pass:** `|P₃₀ − P₀| ≤ 0.5 e` (`0.5 e₁` for multi-interval; `0.5 e_i` returning from Max_i on multiple range). **[V]**
- **Multiple-range only:** after returning to zero from a load > Max₁, immediately switch to the lowest range and keep unloaded for 5 min: `|P₃₅ − P₃₀| ≤ e₁`. **[V]**

### 8.8 Form 6.2 — Creep (A.4.11.1)

- Readings at 0, 5, 15, 30 min (and 1, 2, 3, 4 h if needed). `P = I + ½e − ΔL`; `ΔP = P_t − P₀`.
- **Condition a)** `|ΔP| ≤ 0.5 e` over the 30 min **and** `|P₃₀ − P₁₅| ≤ 0.2 e` → test ends, PASS.
- Otherwise continue to 4 h; **Condition b)** `|ΔP| ≤ |mpe|` throughout 4 h. **Pass = a) or b).** **[V]**
- When b) is needed, the zero-return test is repeated after a fresh 30 min load (per manual steps 23). **[M]**
- **Golden example [M]:** e=5 g, L=15 kg: ΔL = 3.5, 3.0, 2.5, 2.5 g at 0/5/15/30 min → P = 14999.0, 14999.5, 15000.0, 15000.0 g; ΔP = 0.5, 1.0, 1.0 g ≤ 0.5e = 2.5 g; P₃₀−P₁₅ = 0 ≤ 1 g → PASS.
- Creep/zero return are run together for the first 30 min; do not run them right after repeatability (recovery). **[M]**

### 8.9 Form 7 — Stability of equilibrium (A.4.12)

Applies where printing, data storage, zero-setting or tare balancing exists.
- **Printing/storage:** load ≈ 50 % Max; disturb the receptor and immediately command print/store; watch the display 5 s; repeat 5 times. Record first printed/stored value and min/max display values during the 5 s.
  **Pass:** printed/stored value does not deviate more than **1 e** from the readings in the 5 s (only two adjacent values allowed). **[V]**
- **Zero-setting:** apply zero load (< 4 % Max), disturb, release zero; error `E0 = I0 + ½e − ΔL − L0` (with L0 = 10 e when auto-zero in operation); ×5. **Pass: E0 ≤ 0.25 e.** **[V]**
- **Tare balancing:** tare load ≈ 30 % Max (manual: ~50 % of max tare **[M]**), same procedure ×5. **Pass: E0 ≤ 0.25 e.** **[V]**

### 8.10 Form 8 — Tilting (A.5.1)

- **Limiting tilt** by case **[V]** (3.9.1.1): (a) level indicator: tilt at which the bubble edge touches the marked limit; (b) automatic tilt sensor: manufacturer's value (sensor must blank display/alarm and inhibit print/transmission); (c) otherwise **50/1000** any direction; (d) mobile outdoor: tilt sensor or cardanic suspension. Class I: needs levelling device + level indicator but is **not tested**. Fixed-position and freely suspended instruments are not tested.
- **Loads:** unloaded (not for class II unless direct sales), a load at the lowest MPE-change point (class I = 50 000 e, II = 5000 e, III = 500 e, IIII = 50 e **[M]**), and Max (or near). 5 positions v = 1…5 (reference + four tilt directions), repeat readings. **[M]**
- **Formulas:** `P_v = I_v + ½e − ΔL_v`; `P°_v` = P_v corrected for the zero deviation prior to loading.
- **Pass:** unloaded: `|P₁ − P_v|max ≤ 2 e` (not class II); loaded: `|P°₁ − P°_v|max ≤ |mpe|`. **[V]**
- Older manual used 0.2 % tilt and 5 % without an indicator — those belong to the 1992 edition; use the 2006 rules above. **[M→superseded]**

### 8.11 Form 9 — Tare (weighing test) (A.4.6.1)

- Two tare values: first tare ≥ Min plus a small weight near a changeover point; second tare a different value. For each: press tare, then a weighing test with ≥ 5 **net** loads: near Min, maximum possible net load, MPE change points. **[M]**
- **Formulas:** as 7.2; loads L are net loads. **Pass:** `|Ec| ≤ |mpe(net L)|` (3.5.3.3). MPE not applied to *preset tare* values.
- **Tare-setting accuracy (A.4.6.2):** non-auto/semi-auto: `E0 = ½e − ΔL0 ≤ 0.25 e`; automatic: with 10 e, `E0 = I0 + ½e − ΔL0 − L0`. Electronic and analog: ±0.25 e; mechanical with digital indication: better than ±0.5 d (4.6.3). e = e₁ for multi-interval. **[V]**
- **Preset tare rounding [M]:** key in a tare with finer resolution than e (e.g. 402 g with e = 5 g): display must round (→ 400 g) or reject; internal value must also be rounded (error must not change by the unrounded difference).
- Tare-weighing device: dT = d (4.6.2). **[V]**

### 8.12 Form 10 — Warm-up time (A.5.2)

- Instrument disconnected **≥ 8 h** (record duration; 8 h [M]). Reconnect; **as soon as the indication has stabilised set to zero**. No pre-load. Times (from first appearance of indication): **0, 5, 15, 30 min**; at each time read the unloaded error `E0` (10 e/20 e on if auto-zero) and the error at Max `EL`.
- **Pass:** `|EL − E0| ≤ |mpe|` at each time. **[V]** (form 10)
- Golden example **[M]**: E0 = 0.8 g, EL = −1.0 g → EL−E0 = −1.8 g; mpe 7.5 g → PASS.

### 8.13 Form 11 — Voltage variations (A.5.4)

- Choose supply category (6.6). Compute lower/upper limits; test at **reference value, lower limit, upper limit**. If the instrument has more than one supply category, repeat per category.
- At each voltage: zero (10 e) and a test load; `Ec = E − E0`. **Pass:** `|Ec| ≤ |mpe|`. **[V]**
- Also check (checklist) below-limit behaviour: continues correctly or shows no weight. **[V]**

### 8.14 Forms 12.1-12.7 — Electrical disturbances (B.3)

Pass rule for all: **no significant fault (> e)**, or the fault is *detected and acted upon* (explain in remarks). Record load (a test load, e.g. ~ 50 % of Max, and material of load for RF tests), indication without disturbance and during disturbance. **[V]**
Parameters **[V]** (from the printed forms):

| Form | Test | Levels / settings |
|---|---|---|
| 12.1 | AC mains dips & short interruptions | Utest = U_nom (or average of U_min/U_max). Rows: 0 % for 0.5 cycle; 0 % for 1 cycle; 40 % for 10 cycles; 70 % for 25 cycles; 80 % for 250 cycles; **0 % for 250 cycles**. ≥ 10 disturbances, repetition interval ≥ 10 s |
| 12.2a | Bursts, mains | **1 kV** on L, N, PE each to ground; each polarity **1 min** |
| 12.2b | Bursts, I/O & communication lines | **0.5 kV**; each cable/interface, each polarity **1 min** |
| 12.3a | Surges, AC mains | 3 positive + 3 negative at angles 0°, 90°, 180°, 270°; L–N **0.5 kV**; L–PE **1 kV**; N–PE **1 kV** |
| 12.3b | Surges, other supply | 3 pos + 3 neg; L–N 0.5 kV; L–PE 1 kV; N–PE 1 kV |
| 12.4a | ESD, direct | Contact discharge **2, 4, 6 kV**; air discharge **8 kV**; both polarities; ≥ 10 discharges, interval ≥ 10 s; record failing test point |
| 12.4b | ESD, indirect | Contact only, horizontal and vertical coupling plane, 2/4/6 kV, both polarities |
| 12.5 | Radiated EM fields | **10 V/m**, 80 % AM 1 kHz sine; **26–2000 MHz** if 12.6 cannot be applied, else **80–2000 MHz**; polarisation vertical & horizontal; facings front/right/left/rear; record sweep rate, load material; record failing frequency |
| 12.6 | Conducted RF | **0.15–80 MHz**, **10 V emf** (50 Ω), 80 % AM 1 kHz sine; each cable/interface |
| 12.7a | Vehicle 12 V supply transients | 2a +50 V; 2b +10 V (only if connected via ignition switch); 3a −150 V; 3b +100 V; 4 −7 V |
| 12.7a | Vehicle 24 V supply transients | 2a +50 V; 2b +20 V; 3a −200 V; 3b +200 V; 4 −16 V |
| 12.7b | Capacitive/inductive coupling (non-supply lines) | 12 V system: a −60 V, b +40 V; 24 V system: a −80 V, b +80 V |

The disturbance tests are **recorded, not computed** (as the nawi-testbench project also does): the software's job is the data-entry grid, the "significant fault?" yes/no with the required remark, the auto-warning if |I_disturbed − I_undisturbed| > e and the engineer selected "No", and the verdict.

### 8.15 Form 13 — Damp heat, steady state (B.2)

Three weighing-performance pages: a) **initial test at reference temperature** (20 °C), b) **test at high temperature (upper temperature limit) and 85 % relative humidity**, c) **final test at reference temperature**. Each page: `Ec = E − E0`, **pass `|Ec| ≤ |mpe|`** (form). **[V]** Cycle length/duration and stabilisation come from B.2 and IEC 60068-2-3 (steady-state: 2 days at 85 % RH) **[C]** — read B.2 and put the values in the rule set.
Non-electronic instruments: not applicable. Purely digital modules: exempt (3.10.2.2).

### 8.16 Form 14 — Span stability (B.4)

- Test load: **the same traceable load (Max or near Max)** for all measurements. Minimum **8 measurements** for electronic instruments, at regular intervals before, during and after the other performance tests (not the endurance test) **[M]**. Suggested schedule **[M]**:

| Measurement | Taken after | Condition |
|---|---|---|
| 1 | initial weighing performance | instrument on ≥ 5 h |
| 2 | warm-up test | power **off ≥ 8 h**, then **on ≥ 5 h** |
| 3 | temperature tests (static temp + no-load effect) | ≥ 16 h after end |
| 4 | damp heat | ≥ 16 h after end |
| 5 | short power reductions, bursts, ESD | any time after |
| 6-8 | free, but include one power off/on and cover the whole campaign | |

- Each measurement: `E0 = I0 + ½e − ΔL0 − L0`, `EL = IL + ½e − ΔL − L`, `EL − E0`. Measurement 1: **5 loadings**; range `(EL−E0)max − (EL−E0)min`; if `≤ 0.1 e` then **one loading** is enough for subsequent measurements, otherwise 5 loadings each time with the same weights. **[V]**
- Plot the average error for each measurement (chart on form p. 45: axis −1.5 e … +1.5 e, marks T = after temperature, D = after damp heat, P = after power disconnection). **[V]**
- **Pass (implement conservatively):** variation of average errors `max(avg) − min(avg) ≤ 0.5 × |mpe|` at the test load. In the manual's example, allowable variation = 3.75 g = 0.5 × 7.5 g mpe. **[M]** Confirm exact wording in R 76-1 5.3.3/B.4 **[C]**. Also apply corrections for temperature/pressure changes (class I) and log them in the "Corrected value" column.
- Automatic span-adjustment device: record whether it was activated at each measurement.

### 8.17 Form 15 — Endurance (A.6)

- Applies only when **Max ≤ 100 kg** (3.9.4.3). Done **last**. Steps: a) initial weighing test, b) performance of the loading cycles (number of loadings and load applied — **[C] read A.6**), c) final weighing test.
- **Durability error** = `|Ec_initial − Ec_final|` at each load. **Pass:** ≤ |mpe|. **[V]**

### 8.18 Form 16 — Examination of the construction

Free text + photos: description, main components, remarks useful for verification authorities. **[V]**

### 8.19 Zero and tare device checks (part of checklist 17.1, tests A.4.2 / A.4.6.2) **[M for procedures, V for limits]**

| Check | How | Pass |
|---|---|---|
| Initial zero-setting range | power on with increasing load until it no longer zeros; also negative part (remove receptor or add weights) | Range as % Max recorded; > 20 % ⇒ supplementary test |
| Zero-setting range (non-auto/semi-auto/auto) | as above with zero key / waiting ≥ 5 s | overall effect not to alter Max; limit per 4.5.1 **[C]** |
| Zero-tracking range with/without tare | water-drip feeder or 0.2 d weights at 2 s intervals | per 4.5.1 / 4.5.7 (up to 4 % Max after tare) **[V for 4 %; C for rest]** |
| Zero-tracking speed | drip time for ≥ 5 d change | ≤ 0.5 d/s; a zero-indicating device is mandatory if speed < 0.25 d/s **[M]** |
| Zero-indicating device | 0.1 e weights, find points to 0.05 e | deviation ≤ 0.25 e **[V]** |
| Accuracy of zero setting | 4.5.2 | E0 ≤ 0.25 e |
| Automatic zero-setting | operates only when stable and indication stable below zero ≥ 5 s | checklist 4.5.6 **[V]** |

### 8.20 Checklist (form 17) — data to seed

Store as rows in `checklist_items` (code, text, clause, applicability). Groups **[V]**:

- **17.1** all types except non-self-indicating: descriptive markings (7.1.1-7.1.5.2), verification marks and sealing (7.2, 4.1.2.4-4.1.2.6), documentation (8.2), indicating device (4.2-4.4, 3.4), differences between results (3.6.3, 3.6.4), tilting features (3.9.1.1), zero/tare/preset tare/locking/multiple-range/selection devices (4.5-4.11), plus-minus comparators (4.12), mechanical counting (4.17), modes of operation (4.20).
- **17.2** direct sales to the public, price-computing and labelling (4.13, 4.14, 4.16, 4.18).
- **17.3** electronic (5.1.1, 5.2, 5.3.1, 5.3.6).
- **17.4** software-controlled (5.5.1, 5.5.2, 5.5.3; Annex G).

Key content to code as checklist items:

- **Compulsory markings (7.1.1):** manufacturer's mark/name, accuracy class, Max (Max₁…), Min, e (e₁…). **Compulsory if applicable (7.1.2):** agent, serial number, identification of separate units, type approval mark, d (if d < e), software identification, T (subtractive tare only if T ≠ Max), Lim (if Lim > Max + T), special temperature limits, counting ratio, platform/load ratio, plus/minus range. **Additional (7.1.3):** "not for direct sales to the public", "to be used exclusively for…", etc. **Presentation (7.1.4):** indelible, easily readable, grouped, Max/Min/e/d permanently displayed near the display, sealable. Verification mark area ≥ 150 mm² (stamp) or ø ≥ 15 mm (self-adhesive) (7.2.2).
- **Indication (4.2-4.4):** scale interval form (1, 2 or 5) × 10^k; same interval on all displays/printers/tare devices; decimal sign position; at most one non-significant zero rule; **no indication above Max + 9 e**; **no indication below zero (−20 d accepted)** unless a tare device is in operation; digital changing ≤ 1 s; stable-equilibrium rules; printed figures ≥ 2 mm high; units to the right of value.
- **Zero:** 4.5.1-4.5.7 (see 8.19). **Tare:** 4.6.1-4.6.11 (operating range, NET designations, subtractive tare not usable above Max, multiple-range behaviour, printing G/B/N/T designations). **Preset tare:** 4.7.
- **Direct sales to public (4.13):** two displays or one for both; figure height **≥ 9.5 mm** for the customer; non-automatic zero-setting only with a tool; automatic tare not allowed; alarm on significant fault; etc.
- **Price computing (4.14):** `|W × U − P| ≤ e × U` for price scales; rounding to nearest price interval; display/freeze times (≥ 1 s after stable weight; freeze ≤ 3 s after unloading); printing rules.
- **Electronic (5.x):** interfaces must not allow functions or data to be inadmissibly influenced by peripherals; no display of data mistakable for weighing results; no falsification of results; no change of adjustment.
- **Software (5.5, Annex G):** manufacturer's declaration (fixed hardware/software environment, no modification after securing); documentation of legally relevant functions; software identification clearly assigned and displayable; protection against accidental/intentional changes; separation of legally relevant software; audit trail; data storage device requirements (5.5.3): sufficient capacity, all information to reconstruct a weighing, checksum/signature, identification number on the print-out.

> Do **not** type all ~200 lines by hand from memory. Copy the checklist text from R 76-2 pages 50-62 into a `checklist_seed.json` (code, clause, text, group, applicability) and load it.

---

## 9. Validation catalogue (server-side, mirrored in the UI)

Severity **ERROR** blocks saving/submitting; **WARN** saves but travels with the record into the report ("Implausible ones are saved with a warning that follows them into the report" — the same idea used by nawi-testbench).

### 9.1 Instrument (checked when the form is saved)

| ID | Rule | Sev. | Clause |
|---|---|---|---|
| V-INS-001 | Class ∈ {I, II, III, IIII} | ERR | Table 1 |
| V-INS-002 | For each range: `n = Max/e` inside Table 3 [n_min, n_max] for the class and e band | ERR | 3.2 |
| V-INS-003 | `Min ≥ Table 3 factor × e` (or × d if auxiliary device); grading instrument: 5 e | ERR | 3.2, 3.4.3 |
| V-INS-004 | `d ≤ e`; without auxiliary device `e = d` | ERR | 3.1.2, Table 2 |
| V-INS-005 | With auxiliary device: only class I/II, `d < e ≤ 10 d`, `e = 10^k kg`; not allowed on multi-interval | ERR | 3.4 |
| V-INS-006 | e (and d) of form (1, 2, 5) × 10^k | ERR | 4.2.2.1 |
| V-INS-007 | Multi-interval: `e_{i+1} > e_i`; `Max_i / e_{i+1} ≥ 50000/5000/500/50` for I/II/III/IIII (all but the last range) | ERR | Table 4 |
| V-INS-008 | Max > Min > 0; ranges increasing | ERR | 3.3 |
| V-INS-009 | Lim ≥ Max + T₊ if entered | ERR | 7.1.2 |
| V-INS-010 | U_min ≤ U_nom ≤ U_max; frequency > 0 | ERR | – |
| V-INS-011 | Electronic instrument must have a power-supply category | ERR | 3.9.3 |
| V-INS-012 | Special temperature range span ≥ 5 (I) / 15 (II) / 30 (III, IIII) °C | ERR | 3.9.2.2 |
| V-INS-013 | Class II or III e ≥ 0.1 g with n_max above the limit for outdoor use: `n > 3000` outdoors → warn (weighbridge e ≥ 10 kg recommended) | WARN | 3.9.5 note |
| V-INS-014 | Class I with e < 1 mg → warn "not normally feasible to test" | WARN | Table 3 note |
| V-INS-015 | Sum of squares of module fractions ≤ 1; per-module p within [0.3, 0.8] when more than one module contributes, digital-only p may be 0, weighing module p may be 1 | ERR | 3.10.2.1 |

### 9.2 Evaluation setup

| ID | Rule | Sev. |
|---|---|---|
| V-EVL-001 | Rule set exists and is active on evaluation start; store id + sha256 | ERR |
| V-EVL-002 | Every weight used has `|weight error| ≤ mpe/3` for the loads it is used at (or uncertainty for E2 or better) | ERR (3.7.1) |
| V-EVL-003 | Equipment calibration certificate valid on the test date | ERR |
| V-EVL-004 | Multiple-range instrument: exactly one range per evaluation (separate reports) | ERR |
| V-EVL-005 | Class I: barometric pressure recorded on every test page | ERR |
| V-EVL-006 | Temperature/humidity present at start and end | WARN |
| V-EVL-007 | Absolute humidity ≤ 20 g/m³ during static-temperature tests | WARN [M] |
| V-EVL-008 | Test date within evaluation period | WARN |

### 9.3 Observations

| ID | Rule | Sev. |
|---|---|---|
| V-OBS-001 | Numeric fields parse as decimals; no negative L; ΔL ≥ 0 | ERR |
| V-OBS-002 | `L ≤ Max + T₊` (`≤ Max` for gross) | ERR |
| V-OBS-003 | Indication I is a multiple of the step `d` (± tolerance for analog) | ERR |
| V-OBS-004 | `0 ≤ ΔL ≤ step` for changeover readings (ΔL larger than one step means the changeover was mis-recorded) | ERR |
| V-OBS-005 | `|I − L| > 10 e` → probable typo | WARN |
| V-OBS-006 | Load exactly at a scale-interval change or at blanking limit | WARN [M] |
| V-OBS-007 | Weighing pages: coverage of Min…Max and MPE change points; ≥ 5 loads (≥ 10 initial) | WARN |
| V-OBS-008 | Increasing and decreasing series both present | WARN |
| V-OBS-009 | Repeatability: 10 values per load (3 if Max > 1000 kg) | ERR/WARN |
| V-OBS-010 | Creep: required time points present for the branch chosen | ERR |
| V-OBS-011 | Span stability: same test load used in all measurements; ≥ 8 measurements for electronic | ERR/WARN |
| V-OBS-012 | Tilt used equals the limiting value defined for the case (8.10) | ERR |
| V-OBS-013 | Disturbance: if |I_dist − I_ref| > e and "significant fault = No" and no remark | ERR |
| V-OBS-014 | Endurance final test present only after all other tests are saved | WARN |
| V-OBS-015 | Dates/times monotonic within a test (start ≤ max ≤ end) | ERR |
| V-OBS-016 | Auto-zero status selected → zero row must be at 10 e / "out of working range" when status is *in operation* | WARN |
| V-OBS-017 | `initial_zero_gt_20pct = true` ⇒ supplementary weighing page exists | ERR at submit |
| V-OBS-018 | Same page + same L entered twice | WARN |

### 9.4 Guard against dangerous numeric mistakes

- Parse all numbers with `Decimal`; reject `NaN`, `Infinity`, scientific notation surprises.
- Units: store the instrument unit once; all observation fields in that unit; convert only via `Decimal` factors (1 kg = 1000 g; 1 g = 1000 mg; 1 t = 1000 kg; 1 ct = 0.2 g).
- Boundary tests must use `<=` exactly as in Table 6 (e.g. m = 500 e is in the 0.5 e band for class III).

---

## 10. Report generation

### 10.1 Report model (single source of truth)

Build a JSON "report model" from the database, then render it three ways (HTML→PDF, DOCX, JSON export).

```jsonc
{
  "report_no": "LM/NAWI/2026/0001",
  "ruleset": {"id":"oiml-r76-2006","sha256":"…"},
  "laboratory": {...}, "instrument": {...}, "ranges": [...],
  "equipment": [...],
  "summary": [ {"form":"1","test":"Weighing performance","page":"5/38","verdict":"PASSED","remarks":""}, ... ],
  "tests": [ {"form":"1","condition":"Initial 20 °C","environment":{...},"rows":[...],"verdict":"PASSED","warnings":[...]} ],
  "checklist": [...],
  "attachments": [...],
  "approval": {"approver":"…","at":"…","hash":"sha256:…","qr":"data:image/png;base64,…"}
}
```

### 10.2 Layout = R 76-2 pages **[V]**

Order: header with page counter `Report page n/N` → General information (p.6-7) → Test equipment (p.8) → Summary of type evaluation (p.9) → tests 1 … 15 in order → 16 Construction → 17 Checklist → attachments (photos, sketches).

Symbols to reproduce **[V]**: PASSED = X in PASSED box; FAILED = X in FAILED box; not applicable = "– –". Each test page prints the formulas (`E = I + ½ e − ΔL − L`, `Ec = E − E0`), the mpe column and the "Check if |Ec| ≤ |mpe|" line with the result.

Every page footer: `OIML R 76-2:2007 format · Report no. · Rule set id · page n/N`.

### 10.3 PDF (WeasyPrint)

```python
from weasyprint import HTML
html = template.render(report=report_model)
HTML(string=html, base_url=static_dir).write_pdf(out_path,
        pdf_variant="pdf/a-3b")     # archival-friendly
```
Use CSS `@page { size: A4; margin: 15mm; @bottom-center { content: counter(page) "/" counter(pages) } }`. Keep one test per page (`page-break-before: always`). Embed fonts (Noto Sans / Noto Sans Devanagari if you add Hindi).

### 10.4 Word (.docx) with python-docx

- Build with the same report model. One helper per table type (header block, ↑/↓ error table, checklist table).
- Use real Word tables (not images) so the lab can edit.
- Put lab logo in the header; page number field in footer.
- Add a watermark/text "DRAFT – NOT APPROVED" unless `status = APPROVED`.
- Test the export opens in Word and LibreOffice.

### 10.5 Attachments

- Accept JPG/PNG/WebP/PDF; max 10 MB each; verify magic bytes (not just extension); compute SHA-256; generate thumbnail (Pillow); strip GPS EXIF.
- Photo types: full instrument, data plate/markings, test setup (e.g. ESD test points, radiated set-up), sketches of eccentricity positions, level indicator, seal/verification mark area.
- Captions; "include in report" flag; images embedded in PDF/DOCX at the relevant test page or in an Annex.

### 10.6 Digital signature (optional, two levels)

1. **Application level (default):** on approval compute `approval_hash = SHA-256(canonical_json(instrument, observations, verdicts, ruleset_sha256))`; store approver id + time; print hash and QR to `/verify/<report_no>` (public page shows report no., type, outcome, date, hash; nothing confidential).
2. **PDF level (optional):** sign with **pyHanko** using a .p12 or PKCS#11 hardware token (e.g., a Class 3 Digital Signature Certificate). Visible signature field on the last page; timestamp authority optional. Mark `report_exports.signed = true`.

---

## 11. Repository, search, dashboard

### 11.1 Repository and history
- Every evaluation is kept forever (soft-delete only). Exports are versioned (`report_exports.version`) with their SHA-256.
- Instrument page shows its **test history**: all evaluations (type approval, verification), outcomes, dates, links.
- Re-evaluation is a *new* evaluation record, never an overwrite.

### 11.2 Search
Filters: report no., application no., manufacturer, applicant, model/type designation, serial no., class, category, status, outcome, purpose, date range, tester, reviewer, "contains failed test X". Implementation: PostgreSQL full-text (`tsvector`) on textual fields + indexed filters; paginate; export result list to CSV.

### 11.3 Dashboard (widgets)
- Tiles: Draft / In progress / Under review / Returned / Approved this month / Failed this month.
- Bar chart: reports by month, split by outcome.
- Table: "My tasks" (returned to me, waiting for my review).
- Ageing: evaluations in progress > 30 days.
- Pass rate by test kind (which test fails most) — good demo material.
- Equipment: calibration due within 30 days.
- Recent activity feed from `audit_log`.

---

## 12. API (REST, JSON) — endpoint list

```
POST /api/auth/login              POST /api/auth/refresh        POST /api/auth/logout
GET  /api/me                      POST /api/me/password

GET/POST      /api/users          PATCH /api/users/{id}         (ADMIN)
GET/POST      /api/laboratories   GET/POST /api/parties
GET/POST      /api/equipment      PATCH /api/equipment/{id}

GET/POST      /api/instruments    GET/PATCH /api/instruments/{id}
GET           /api/instruments/{id}/history
POST          /api/instruments/validate            # runs V-INS rules without saving
GET           /api/instruments/{id}/applicability  # which tests apply (from rule set)

GET/POST      /api/evaluations                     GET/PATCH /api/evaluations/{id}
POST          /api/evaluations/{id}/submit         POST /api/evaluations/{id}/return   POST /api/evaluations/{id}/approve
GET           /api/evaluations/{id}/suggest-loads  # section 7.4
GET           /api/evaluations/{id}/temperature-schedule   # 8.3
GET           /api/evaluations/{id}/completeness   # what is missing to submit

GET/POST      /api/evaluations/{id}/tests          PUT /api/tests/{test_id}
POST          /api/tests/{test_id}/evaluate        # dry-run engine: returns computed values + warnings (live readout)
GET/PUT       /api/evaluations/{id}/checklist

POST          /api/evaluations/{id}/attachments    GET /api/attachments/{id}    DELETE ...
POST          /api/evaluations/{id}/reports?format=pdf|docx|json
GET           /api/reports/{export_id}/download
GET           /verify/{report_no}                  # PUBLIC

GET           /api/dashboard/summary
GET           /api/search?q=&status=&outcome=&...
GET           /api/rulesets       POST /api/rulesets (ADMIN: upload new JSON, validated against schema)
GET           /api/audit?entity=&id=
```
All list endpoints paginated (`?page=&size=`); errors use a consistent `{code, message, field_errors[]}` body.

---

## 13. Frontend — pages and forms

| Page | Contents |
|---|---|
| Login / change password | |
| Dashboard | section 11.3 |
| Instruments list / detail | table + history tab; wizard **New instrument** (steps: manufacturer & applicant → class & ranges → power & environment → zero/tare devices → printer, software, load cells → review with live validation V-INS) |
| New evaluation | choose instrument, purpose (type approval / verification), MPE context, lab, observer, test equipment; shows the list of tests that apply |
| Evaluation workspace | left rail = list of test pages with status chips (Pending/Passed/Failed/N/A); centre = form; right = **live readout panel** (E, Ec, mpe, ✓/✗ per row, warnings) |
| Test forms (one component per kind, section 8) | see below |
| Checklist | grouped accordion with PASS/FAIL/N/A toggles and remarks |
| Attachments | drag-and-drop uploader with captions |
| Review | reviewer sees summary, warnings, diffs since last return, approve/return with comment |
| Reports | preview (HTML), download PDF/DOCX/JSON, signed badge, QR |
| Search / repository | filter bar + results table |
| Admin | users, labs, equipment, rule sets, audit log |

**Form UX rules that make data entry fast and safe**
- Tables behave like a spreadsheet: Tab/Enter moves to next cell; paste from Excel supported; CSV import with row-by-row rejection report (same validators).
- "Suggest loads" button pre-fills the L column (section 7.4).
- After each row the client calls `/tests/{id}/evaluate` (debounced) and shows E, Ec, mpe and a green/red chip immediately.
- Show the formula and clause next to each verdict (e.g. "Ec = −0.4 g; mpe = 3 g (1.5 e, 2000 e < m ≤ 10 000 e; R 76-1 Table 6) → PASS").
- Unit label always visible; inputs use `inputmode="decimal"`.
- Autosave every 20 s; "unsaved changes" guard.
- Tablet-friendly layout (labs use tablets at the bench); large touch targets.
- Accessibility: labels, focus order, colour + icon (not colour alone).

---

## 14. Security

- Passwords: argon2id; min 12 chars; lockout after 5 failures (15 min); forced change at first login.
- JWT access (15 min) + rotating refresh token in `HttpOnly; Secure; SameSite=Strict` cookie; CSRF token for state-changing requests.
- RBAC enforced in dependencies (`require_role("REVIEWER")`), not only in the UI. Object-level checks (an engineer edits only assigned evaluations).
- Input validation with Pydantic; parameterised SQL only; output escaping in templates (Jinja autoescape).
- File upload hardening (10.5); serve files via signed short-lived URLs; never execute uploads.
- Rate limiting (slowapi) on login and export endpoints.
- Audit log for login, create/update/delete, submit, return, approve, export, rule-set change. Append-only (DB role without UPDATE/DELETE on `audit_log`).
- Secrets in environment / Docker secrets; TLS everywhere; security headers (CSP, HSTS, X-Content-Type-Options).
- Backups nightly (`pg_dump`) + file store snapshot; restore drill documented. Retention policy configurable (archive after N years).
- Privacy: no personal data except staff names/emails; applicant data limited to what the report needs.

---

## 15. Testing strategy (this is what convinces reviewers)

### 15.1 Layers
1. **Unit tests for the engine** (hundreds of cases, no DB).
2. **Golden tests** — published worked examples reproduced to the last digit (15.2).
3. **Property-based tests** (hypothesis): MPE is monotone non-decreasing in load within a range, `mpe(in_service) == 2 × mpe(initial)`, `Ec` shift invariance (adding a constant to all I and L doesn't change E), rounding never changes verdict when ΔL is consistent.
4. **API tests** (pytest + httpx): RBAC matrix, state machine, validation errors.
5. **Report tests**: PDF has N pages, contains the rule-set id, formulas; DOCX opens with python-docx and has expected tables; snapshot the HTML.
6. **E2E** (Playwright): login → create instrument → evaluation → enter all tests → submit → approve → download PDF.
7. **Cross-check with a spreadsheet**: reproduce two full evaluations independently in Excel and compare every number.

### 15.2 Golden cases you can use immediately

**G1 — Table 6 boundaries (class III, e = 1 g):** mpe(500 g)=0.5 g; mpe(501 g)=1 g; mpe(2000 g)=1 g; mpe(2001 g)=1.5 g; mpe(10000 g)=1.5 g; mpe(10001 g)→ error "beyond Table 6".
**G2 — Class I/II/IIII boundaries** analogous (50 000/200 000; 5000/20 000/100 000; 50/200/1000).
**G3 — Multi-interval example from R 76-1 3.3.4 [V]:** class III, e=1/2/10 g, Max=2/5/15 kg → the MPE table in 6.4. Also n₁=2000, n₂=2500, n₃=1500; check `Max₁/e₂ = 1000 ≥ 500` and `Max₂/e₃ = 500 ≥ 500` (Table 4 OK).
**G4 — Repeatability [M]:** e=5 g class III multi-interval 6/15 kg (e₁=2 g, e₂=5 g), load 7.5 kg: ten ΔL values {2.5,2.5,2.5,3.0,2.5,2.5,2.5,3.0,2.5,2.5} g → P values 7.5000 or 7.4995 kg, Pmax−Pmin=0.5 g, mpe=5 g → PASS. Load 15 kg: ΔL {3.0,3.0,3.0,3.0,3.0,3.5,3.0,3.0,3.5,3.0} g → range 0.5 g, mpe=7.5 g → PASS.
**G5 — Temperature no-load [M]:** ½e=1 g near zero: (20.1 °C, I=20 g, ΔL=1.0 g)→P=20.0 g; (40.3 °C, I=22 g, ΔL=0.4 g)→P=22.6 g; ΔP=2.6 g, ΔT=20.2 → 0.6436 g per 5 °C < e → PASS. (Use only this first pair as golden. The −10 °C step in the sample also passes; the 5 °C row of the sample sheet is internally inconsistent, so do not copy it.)
**G6 — Creep [M]:** see 8.8.
**G7 — Warm-up [M]:** E0=0.8 g, EL=−1.0 g → EL−E0 = −1.8 g ≤ 7.5 g.
**G8 — Discrimination digital [M]:** e=d=5 g at 15 kg: I₁=15.000 kg, I₂=15.005 kg → I₂−I₁ = 5 g ≥ d → PASS.
**G9 — Voltage limits:** mains 230 V → lower 195.5 V, upper 253 V; range 100–240 V → reference 170 V, lower 85 V, upper 264 V; battery non-rechargeable 6 V → upper 6 V; 12 V vehicle → upper 16 V.
**G10 — Absolute humidity:** T=33 °C, RH=57 % → 20.2 g/m³ (warn).
**Add your own from a real test sheet** if you can get one from a lab, and keep it as the acceptance test.

> Note: the NMI P 108 sample sheets are useful, but they follow the 1992 edition and contain hand-typed numbers (for instance one MPE cell at 2.00 kg does not match Table 6 for e₁ = 2 g). Trust the standard's Table 6, not the example cells.

### 15.3 Coverage target
Engine ≥ 95 % line coverage and 100 % of clause-tagged rules exercised at least once (add a script that lists rule-set entries with no test referencing them).

---

## 16. Step-by-step build plan (do these in order)

### Phase 0 — Prepare (Day 1-2)
1. Download the documents in section 0. Read R 76-1 clauses 3, 4.5, 4.6, A.4, A.5, B.2-B.4 and R 76-2 fully.
2. Create the git repo; add `README.md`, `.gitignore`, `docs/`.
3. Fill the "to confirm" list (Appendix C) by reading the clauses; update the JSON with **[V]** tags.
4. Try to obtain one real completed lab test sheet from a legal metrology lab (ask your mentor / the Legal Metrology department). Use it as acceptance data.

### Phase 1 — Engine first (Week 1)
1. `python -m venv .venv && pip install fastapi uvicorn sqlalchemy alembic psycopg[binary] pydantic argon2-cffi python-jose weasyprint python-docx pyhanko qrcode pillow jinja2 pytest hypothesis httpx`.
2. Write `rulesets/oiml-r76-2006.json` from section 6 and a JSON-Schema (`schema.json`) that rejects a constant with no `clause`.
3. Implement `units.py`, `classification.py`, `mpe.py`, `error.py` → tests G1-G3.
4. Implement each test module in the order: weighing, eccentricity, repeatability, temperature no-load, creep/zero-return, warm-up, voltage, discrimination, sensitivity, stability of equilibrium, tilting, tare, zero/tare accuracy, damp heat, span stability, endurance, disturbances (grid + rule), checklist → tests G4-G10.
5. `evaluate.py` — orchestrates all tests, applicability, outcome logic (7.5).
6. `validate.py` — V-INS, V-EVL, V-OBS (section 9).
**Exit criterion:** `pytest` green; engine reproduces all golden cases; no float anywhere (`grep -R "float(" app/engine` returns nothing).

### Phase 2 — Backend (Week 2-3)
1. DB models + Alembic migration for section 4 tables; seed roles, lab, an admin user, the rule set, checklist items.
2. Auth (login/refresh/logout, argon2, lockout) and RBAC dependencies.
3. CRUD: users, labs, parties, equipment, instruments (+ranges), evaluations.
4. Test-record endpoints + `/evaluate` dry-run; state machine and submission gate.
5. Attachments (upload, checks, thumbnails).
6. Audit logging middleware.
7. API tests for RBAC and state transitions.

### Phase 3 — Frontend (Week 3-5)
1. Vite + React + TS + Tailwind; API client with auth refresh; route guards by role.
2. Instrument wizard → validation messages from `/instruments/validate`.
3. Evaluation workspace with the live readout panel; build the forms in this order: weighing (reuse for tare, damp heat, endurance) → repeatability → eccentricity → temperature no-load → time dependence → discrimination/sensitivity → tilting → warm-up → voltage → span stability → disturbances → checklist → construction/photos.
4. Dashboard, search, repository, review screens.

### Phase 4 — Reports (Week 5-6)
1. Report model builder; HTML template mirroring R 76-2 pages; PDF via WeasyPrint.
2. DOCX generator (python-docx) from the same model.
3. QR + hash + verify page; optional pyHanko signing.
4. Compare rendered PDF against the official R 76-2 layout page by page.

### Phase 5 — Hardening, docs, deployment (Week 7-8)
1. Security checklist (section 14); dependency audit (`pip-audit`, `npm audit`).
2. Docker Compose (section 17); backups; seed/demo data with two full evaluations (one FAIL, one PASS through the whole battery).
3. Write documentation (section 18); record a 5-minute demo video.
4. User acceptance test with an actual lab user; fix findings.

### If you only have ~10 days (hackathon cut)
Day 1-2 rule set + engine core (weighing, eccentricity, repeatability, temperature no-load, creep/zero return, tare, discrimination). Day 3 API + auth. Day 4-6 UI for those tests + live readout. Day 7 PDF + DOCX for those tests. Day 8 dashboard/search. Day 9 seed demo data + docs. Day 10 rehearsal. Mark the remaining tests as "recorded, not computed" (like disturbances) rather than leaving them out, so the report is still complete.

---

## 17. Deployment

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment: { POSTGRES_DB: nawi, POSTGRES_USER: nawi, POSTGRES_PASSWORD_FILE: /run/secrets/db_pw }
    volumes: [ "pgdata:/var/lib/postgresql/data" ]
    secrets: [ db_pw ]
  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg://nawi@db/nawi
      JWT_SECRET_FILE: /run/secrets/jwt_secret
      FILES_DIR: /data/files
    volumes: [ "files:/data/files" ]
    depends_on: [ db ]
    secrets: [ jwt_secret, db_pw ]
  web:
    build: ./frontend            # multi-stage: node build → nginx serving /dist and proxying /api
    ports: [ "443:443", "80:80" ]
    depends_on: [ api ]
volumes: { pgdata: {}, files: {} }
secrets:
  db_pw: { file: ./secrets/db_pw }
  jwt_secret: { file: ./secrets/jwt_secret }
```

- WeasyPrint needs Pango/Cairo libs: in the backend Dockerfile install `libpango-1.0-0 libpangoft2-1.0-0 fonts-noto`.
- Run migrations on start (`alembic upgrade head`); health endpoint `/healthz`.
- HTTPS via Caddy (auto Let's Encrypt) or the organisation's certificate; if deployed on a government cloud, follow its hardening and hosting guidelines **[C]**.
- Nightly backup cron: `pg_dump` + `rsync` of the file volume; test restore monthly.
- Environments: dev (SQLite ok), staging, prod. CI (GitHub Actions): lint (ruff, eslint), tests, build images, `pip-audit`.
- Observability: structured logs (JSON), request IDs, Prometheus `/metrics` (optional), error reporting (Sentry optional).
- Scaling note: workload is small; a single 2 vCPU / 4 GB VM is enough for dozens of users.

---

## 18. Documentation deliverables (the problem statement asks for these)

1. **Architecture document** — diagram from 3.2, module descriptions, data model, sequence diagrams (login, submit, approve, export), technology choices and reasons.
2. **Calculation methodology** — sections 6-8 of this file rewritten as a formal document: symbols, formulas, tables, every pass/fail criterion with its OIML clause, worked examples (G1-G10), the changeover method explanation, rounding rules, decimal-arithmetic policy.
3. **Deployment framework** — section 17, environments, backup/restore, upgrade procedure, monitoring, security controls.
4. **User manual** — per role, with screenshots; "how to enter each test" cheat-sheet.
5. **Rule-set maintenance guide** — section 19.
6. **Test report** — coverage, golden case results, spreadsheet cross-check.
7. **Traceability matrix** — clause → rule-set entry → engine function → test case → report field (generate automatically from clause tags).

---

## 19. Supporting future OIML revisions

1. Copy `oiml-r76-2006.json` → `oiml-r76-<year>.json`; edit only the changed constants/tables; update `clause` tags.
2. Validate with `schema.json` (CLI `python -m app.rulesets.validate file.json`).
3. Add or change engine behaviour only when the *logic* changes; register new test kinds in the catalogue (the UI form generator reads `kind` metadata).
4. Upload via Admin → Rule sets (dry-run runs the full golden suite against the new file and shows a diff of changed constants).
5. New evaluations pick the active rule set; **existing reports stay bound to the rule set they were judged under** (stored `ruleset_id`/`sha256`); a "recompute under another rule set" tool produces a comparison, never overwrites.
6. Keep a `CHANGELOG-rules.md`.
7. Design the report templates so section titles and formulas come from the rule set / report model where possible, so an R 76-2 edition change only needs template edits.
8. Watch the OIML website for R 76 revisions; the ScienceDirect paper on the error model notes R 76 was under revision — check for a current edition before you freeze the rule set. **[C]**

---

## 20. Demo script (5-7 minutes) and things that impress reviewers

1. Log in as ENGINEER → new instrument (class III, 15 kg, e = 5 g): show live validation catching an illegal n.
2. Start a type-approval evaluation: the app lists the tests that apply (electronic → damp heat, disturbances, span stability).
3. Weighing test: press **Suggest loads**; type readings; watch E, Ec, mpe and ✓ appear live; deliberately enter an error at 15 kg → red FAIL with clause.
4. Switch to REVIEWER: return with comment → ENGINEER fixes → REVIEWER approves and signs.
5. Download PDF and Word; open the Word file and edit a remark; scan the QR code → public verification page.
6. Dashboard and search: find the instrument, open its test history.
7. Admin → Rule sets: upload a modified rule set, show the diff and that old reports keep their original rule set.

Impress with: 100 % decimal arithmetic; clause reference next to every verdict; recomputable reports; audit trail; the temperature schedule generator; CSV import with row-level errors; full R 76-2 page order; and honest labelling of anything "recorded, not computed".

---

## 21. Limits of this document (be honest in your submission)

- Items tagged **[C]** were not verified from the retrieved text. Verify them before using the system for real approvals.
- The NMI P 108 manual (source of **[M]** items) is based on the 1992 edition of R 76-1.
- Electromagnetic disturbance tests are data-recording only.
- Nothing here replaces the judgment of the approving authority; the software supports, not replaces, the metrologist.

---

## Appendix A — MPE quick tables (initial verification, in units of e)

| Load m (in e) | Class I | Class II | Class III | Class IIII |
|---|---|---|---|---|
| ±0.5 e up to | 50 000 | 5 000 | 500 | 50 |
| ±1.0 e up to | 200 000 | 20 000 | 2 000 | 200 |
| ±1.5 e up to | no upper limit | 100 000 | 10 000 | 1 000 |

## Appendix B — Sample seed data (for demos and tests)

```json
{
  "instrument": {
    "type_designation": "DemoScale DS-15", "accuracy_class": "III", "indication_type": "SELF",
    "display_kind": "DIGITAL", "range_kind": "SINGLE", "unit": "kg",
    "min_capacity": "0.1", "ranges": [{"idx":1,"e":"0.005","d":"0.005","max":"15"}],
    "tare_minus": "15", "u_nom": "230", "frequency_hz": "50",
    "power_supply_category": ["MAINS_AC"], "temp_min_c": "-10", "temp_max_c": "40",
    "zero_devices": {"semi_automatic": true, "initial": true, "tracking": true},
    "tare_devices": {"balancing": true, "subtractive": true}
  },
  "expected": {"n": 3000, "mpe_at_15kg": "0.0075", "mpe_at_2.5kg": "0.0025 (500 e)"}
}
```
(Check: e = 5 g = 0.005 kg, n = 15 / 0.005 = 3000, inside class III limits (e ≥ 5 g → n between 500 and 10 000); Min 0.1 kg = 20 e ✓; MPE at 15 kg = 3000 e → 1.5 e = 7.5 g ✓; MPE at 2.5 kg = 500 e → 0.5 e = 2.5 g ✓.)

## Appendix C — "Confirm from the standard" checklist (tick each off)

- [ ] Number of test loads for A.4.4 (5 vs 10) and exact selection criteria (A.4.4.1)
- [ ] A.4.4.2 supplementary test when initial zero-setting range > 20 % of Max
- [ ] A.4.4.3 exact wording of P = I + ½ d − ΔL and use of d vs e; direct reading when d ≤ 0.2 e
- [ ] 4.5.1 numeric limits of zero-setting range and zero-tracking (4 % of Max?) and initial zero-setting (20 %?)
- [ ] A.4.10 number of repeatability weighings (10 vs 3 for Max > 1000 kg)
- [ ] A.5.1 tilting positions and procedure in the 2006 edition
- [ ] A.5.3 temperature test sequence (Figure 10/11), waiting times, when the 5 °C step is required
- [ ] A.5.4 test loads for voltage variation; behaviour below limit
- [ ] B.2 damp heat: duration, temperature, humidity, stabilisation
- [ ] B.3.1-B.3.7 exact test levels, durations, criteria (compare with R 76-2 forms in section 8.14)
- [ ] B.4 span stability: number of measurements, spacing, acceptance limit wording (5.3.3)
- [ ] A.6 endurance: number of loadings, load, rate
- [ ] Table 7 usage and Annex C-F rules if you support modules
- [ ] Indian rules: Legal Metrology (Approval of Models) Rules and any DoCA circulars on NAWI type approval and test-report format
- [ ] Whether the DoCA requires the OIML R 76-2 layout exactly or an Indian format with additional fields (ask the problem-statement owner)

## Appendix D — Useful references

- OIML R 76-1:2006, R 76-2:2007 — oiml.org (publications → R 76)
- NMI P 108 procedure manual and NMI R 76-1/R 76-2 (Australia) — industry.gov.au
- nawi-testbench (GitHub, faizanshahid00007) — rule set as data, pure evaluation function, DOCX/PDF export, QR verification
- NAWI-OIML-R76-Compliance-System (GitHub, AdityaDismu) — workflow: register → evaluate → review → report
- Hackathon repos are prototypes; use them only for design ideas.
