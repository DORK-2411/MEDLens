# ARCHITECTURE — MedLens

**Status:** Draft v1
**Related docs:** `PRD.md`

---

## 1. Guiding Principle

> **LLMs extract. Code decides.**

The LLM's only job is pulling raw values out of unstructured text into a strict schema. Every clinically or logically meaningful decision — range comparison, conflict detection, provenance tagging — is a deterministic, pure, unit-tested function with zero dependency on any model call. This is the load-bearing design decision behind every choice below: it's what makes "no invented reference ranges" a structural guarantee instead of a prompt-engineering hope, and it's what makes the hardest parts of the system trivially testable.

---

## 2. High-Level Component Diagram

```
┌──────────────────────────────────────────────┐
│                 Frontend (React)               │
│  - Patient intake form                         │
│  - Report upload                               │
│  - Structured record view (tables, badges)     │
│  - Source/structured side-by-side view         │
│  - Edit/verify UI for extracted fields          │
│  - Summary display                             │
└───────────────────┬────────────────────────────┘
                     │ REST (JSON)
┌───────────────────▼────────────────────────────┐
│              API Layer (FastAPI)                 │
│  - Request/response validation (Pydantic)        │
│  - Auth (if implemented) / rate limiting          │
└───────────────────┬────────────────────────────┘
                     │
┌───────────────────▼────────────────────────────┐
│                 Services Layer                    │
│                                                     │
│  IntakeService                                     │
│    - validates & persists patient-provided fields  │
│                                                     │
│  ExtractionService                                 │
│    - calls LLM with schema-enforced/tool-calling    │
│      structured output                              │
│    - validates response against Pydantic model      │
│      before it ever reaches the DB                  │
│    - isolated behind an interface so it's mockable  │
│      in tests                                        │
│                                                     │
│  RangeEvaluator  [PURE, no I/O]                    │
│    - compare_to_range(value, low, high) -> flag     │
│                                                     │
│  ProvenanceTagger                                  │
│    - wraps any field write with                     │
│      source/confidence/document_id/timestamp        │
│                                                     │
│  ConflictDetector [PURE, no I/O]                   │
│    - diffs patient-reported vs. extracted history   │
│                                                     │
│  SummaryService                                    │
│    - LLM call, tightly constrained prompt           │
│    - post-generation blocklist scan for             │
│      diagnostic/prescriptive language                │
└───────────────────┬────────────────────────────┘
                     │
┌───────────────────▼────────────────────────────┐
│         Data Layer (SQLite/Postgres + ORM)       │
│  Patient / DiagnosticReport / Observation /       │
│  AuditLog                                          │
└────────────────────────────────────────────────┘
```

**Why this layering:** a reviewer should be able to open `range_evaluator.py` and `conflict_detector.py`, see zero imports from `requests`/DB/LLM clients, and immediately trust that these modules are 100% deterministic and fully covered by unit tests. Everything that touches the network or the model lives in `ExtractionService`/`SummaryService`, where tests use mocked responses to verify *your* error handling, not the model's behavior.

---

## 3. Data Model

All models are Pydantic (or equivalent typed models in your chosen language), designed so the LLM extraction step can never silently invent a value — every extractable field is `Optional`, defaulting to `None`.

```python
class Provenance(BaseModel):
    source: Literal["user_provided", "ai_extracted", "ai_generated"]
    confidence: Optional[float] = None       # only meaningful for ai_* sources
    document_id: Optional[str] = None        # source report, if applicable
    extracted_at: datetime
    edited_by: Optional[str] = None          # set if a human corrected this field
    edited_at: Optional[datetime] = None

class Observation(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_raw: Optional[str] = None          # fallback for non-numeric results (e.g. "positive")
    unit: Optional[str] = None
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    reference_range_raw: Optional[str] = None    # exactly as printed, e.g. "8.6-10.2" or "<5"
    flag: Optional[Literal["LOW", "NORMAL", "HIGH", "UNKNOWN"]] = None
    date: Optional[date] = None
    provenance: Provenance

class DiagnosticReport(BaseModel):
    report_id: str
    patient_id: str
    document_id: str
    observations: List[Observation]
    provenance: Provenance

class PatientRecord(BaseModel):
    patient_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    symptoms: List[str] = []
    conditions: List[str] = []
    allergies: List[str] = []
    medications: List[str] = []
    reports: List[DiagnosticReport] = []
    audit_log: List[dict] = []

class Conflict(BaseModel):
    field: str
    patient_reported_value: str
    extracted_value: str
    source_document_id: str
    detected_at: datetime
```

This shape mirrors HL7 FHIR's `DiagnosticReport` → `Observation` nesting conceptually, without requiring a real FHIR server or LOINC/SNOMED code lookups (explicitly out of scope for the hackathon build — see `PRD.md §5`).

---

## 4. Core Pure Functions (build and test these first)

### 4.1 `compare_to_range`

```python
def compare_to_range(
    value: Optional[float],
    range_low: Optional[float],
    range_high: Optional[float],
) -> Literal["LOW", "NORMAL", "HIGH", "UNKNOWN"]:
    if value is None or range_low is None or range_high is None:
        return "UNKNOWN"
    if range_low > range_high:
        return "UNKNOWN"          # malformed/reversed source data — never guess
    if value < range_low:
        return "LOW"
    if value > range_high:
        return "HIGH"
    return "NORMAL"
```

**Required test cases:** below range, above range, within range, on the low boundary, on the high boundary, missing value, missing either range bound, reversed range bounds, negative values, non-numeric `value_raw` routed to `UNKNOWN`.

### 4.2 `detect_conflicts`

```python
def detect_conflicts(
    patient_reported: dict,
    extracted_history: dict,
) -> List[Conflict]:
    """
    Deterministic comparison — e.g. patient states 'no known allergies'
    while a prior extracted report lists an allergy. No LLM call.
    """
```

**Required test cases:** no conflicts, single conflict, multiple conflicts, case/wording variance handled sensibly, empty inputs.

---

## 5. Extraction Pipeline

1. **Ingest** — accept PDF/image upload, store raw file, generate `document_id`
2. **Text/layout extraction** — OCR or direct text extraction, depending on document type
3. **LLM structured extraction** — call the model using its native structured-output/tool-calling mode against the `Observation`/`DiagnosticReport` schema. The prompt instructs: *extract only what's explicitly present; return null for anything not stated; do not calculate or infer missing values.*
4. **Schema validation** — response is parsed into the Pydantic model; anything that fails validation is rejected and logged, never silently coerced
5. **Deterministic post-processing** — `compare_to_range` runs on every observation with a numeric value and range; `ProvenanceTagger` stamps `source=ai_extracted`, confidence, document_id, timestamp
6. **Persist** — structured record written to DB
7. **Human review (optional but recommended)** — reviewer can edit any field; edit updates `edited_by`/`edited_at` and appends to `audit_log`, original AI provenance is preserved for comparison

---

## 6. Summary Generation

- Input: the structured `PatientRecord` (not raw report text) — this keeps the summary grounded in already-validated structured data
- Prompt is explicitly constrained: no diagnosis, no treatment/medication guidance, uncertain findings framed as "worth discussing with your doctor"
- Output is tagged `source=ai_generated`
- A lightweight post-generation check scans for a blocklist of diagnostic/prescriptive phrasing patterns as a smoke test — not a guarantee, but a documented safeguard and a good talking point for judges

---

## 7. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend | FastAPI | Pydantic-native, fast to build, clean for reviewers |
| LLM integration | Any provider with structured-output/tool-calling support | Avoids hand-parsing free-text JSON out of prompts |
| Database | SQLite (hackathon) / Postgres (if time allows) | Zero-setup, easy to swap later via ORM |
| ORM | SQLModel or SQLAlchemy | Typed, integrates cleanly with Pydantic |
| Frontend | React | Component-based, easy side-by-side views |
| Testing | pytest | Focus on pure functions first, mocked LLM responses second |

---

## 8. Security & Privacy Posture (hackathon-scoped, explicitly documented)

This is a prototype, not a HIPAA-compliant system. What's actually implemented and documented in the README:
- No PHI written to logs
- Minimum-necessary data sent to the LLM API per request
- Clear disclaimer in the UI that outputs are informational, not medical advice
- Audit trail of human edits to extracted data

What's explicitly **out of scope** and named as future work: signed BAAs, encryption-at-rest infrastructure, full RBAC, HIPAA-grade audit logging, real terminology-code mapping (LOINC/SNOMED).

---

## 9. Testing Strategy

| Layer | Approach |
|---|---|
| `compare_to_range`, `detect_conflicts` | Full branch-coverage unit tests, no mocking — these are pure functions |
| `ExtractionService` | Unit tests with mocked LLM responses covering: well-formed output, missing fields, malformed/schema-invalid output, empty response |
| `SummaryService` | Test that constrained prompt + blocklist scan reject/flag diagnostic-shaped output |
| Intake → structured record | One or two integration tests covering the full happy path |
| API layer | Validation tests (bad input types, missing required fields) |

---

## 10. Build Order (see `PRD.md` for feature prioritization rationale)

1. Data models
2. `compare_to_range` + tests
3. Patient intake (frontend + API)
4. `ExtractionService` with schema-enforced LLM output
5. `ProvenanceTagger`
6. Structured record UI with provenance badges
7. `detect_conflicts` + tests
8. `SummaryService` with constrained prompt
9. Human edit/verify UI + audit log
10. FHIR-shaped export / PDF export
11. *(Time permitting)* source-document highlighting view
