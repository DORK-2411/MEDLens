# MedLens — Master Build Plan

**Goal:** Build a working, well-tested, code-review-clean AI clinical record structuring app. Everyone in the hackathon has the same problem statement — you win on execution quality, safety rigor, and a couple of sharp, *actually-working* differentiators, not on feature count.

---

## 1. Non-Negotiable Design Principle

> **LLMs extract. Code decides.**

The LLM is only ever allowed to pull raw values out of text. Every decision that matters clinically or logically — range comparisons, conflict detection, provenance tagging — is done by deterministic, unit-tested Python/TS functions that never call an LLM. This single principle:
- satisfies "reference-range awareness... should not invent ranges"
- satisfies "must not present uncertain information as fact"
- makes the hardest parts of your app trivially unit-testable (huge for the code-quality/test rubric)
- is a genuinely strong story to tell judges: *"our app cannot hallucinate a lab flag — here's the pure function and its test suite."*

Everything below is built around this principle.

---

## 2. Scope Decision (What to build vs. skip)

### Tier 1 — Build these, fully working and tested
| Feature | Why |
|---|---|
| Patient intake with validation | Core requirement |
| LLM extraction with schema-enforced structured output (Pydantic/JSON schema) | Prevents malformed/hallucinated fields |
| Deterministic `RangeEvaluator` (low/normal/high) | Core requirement, safety-critical, easiest to test exhaustively |
| Provenance tagging on every field (`user_provided` / `ai_extracted` / `ai_generated` + confidence) | Core requirement, cheap, high trust value |
| Patient-friendly AI summary (prompt-constrained: no diagnosis/treatment language) | Core requirement |
| Human verification/editing of extracted fields | Bonus feature, cheap, huge trust signal |

### Tier 2 — Build if Tier 1 is solid, keep lightweight
| Feature | Scoped-down approach |
|---|---|
| FHIR-*shaped* output | Mirror `DiagnosticReport` → `Observation` JSON structure. **Skip** real LOINC/SNOMED code lookups — mention as future work |
| Deterministic conflict detection | Plain comparison function (patient-reported vs. extracted history), **not** a multi-agent framework |
| Confidence indicators in UI | Color-coded badges next to AI-extracted fields |
| Export to PDF/JSON | Straightforward, good demo value |
| Timeline / audit log | Simple append-only table of edits with user+timestamp |

### Tier 3 — Only if time remains, high risk of eating your whole timeline
| Feature | Note |
|---|---|
| Bounding-box click-to-highlight source traceability | Start with a static/simpler overlay before attempting full interactive pdf.js zoom |
| Multi-page table stitching | Only touch if your actual test PDFs need it — this is a genuinely hard layout problem |
| Real LOINC/SNOMED semantic mapping | Needs a terminology DB most teams won't have time to integrate correctly |
| LangGraph multi-agent workflow | The *outcome* (conflict detection) is Tier 2; the multi-agent *implementation* adds fragility without added judge-visible value |

**Rule of thumb during the hackathon:** if a Tier 3 item is at risk of shipping half-broken, cut it. A judge will always prefer 6 features that work over 10 where 4 are visibly flaky.

---

## 3. Architecture

```
┌─────────────────────────────┐
│   Frontend (React)          │
│   - Intake form              │
│   - Structured record view   │
│   - Source/structured        │
│     side-by-side view        │
│   - Edit/verify UI            │
└───────────┬─────────────────┘
            │ REST/JSON
┌───────────▼─────────────────┐
│   API layer (FastAPI)        │
│   - Request validation        │
│     (Pydantic)                │
└───────────┬─────────────────┘
            │
┌───────────▼─────────────────────────────────────┐
│                 Services layer                    │
│                                                     │
│  IntakeService        — validates patient input    │
│  ExtractionService    — calls LLM w/ schema output  │
│                          (isolated behind interface)│
│  RangeEvaluator (PURE)— compareToRange(value,range) │
│  ProvenanceTagger     — wraps a field w/ source+    │
│                          confidence + timestamp     │
│  ConflictDetector(PURE)— diffs reported vs extracted│
│  SummaryService       — LLM call, constrained prompt│
│                          (no diagnosis language)    │
└───────────┬───────────────────────────────────────┘
            │
┌───────────▼─────────────────┐
│   Data layer (SQLite/Postgres)│
│   Patient / Report /          │
│   Observation / AuditLog      │
└───────────────────────────────┘
```

**Why this shape matters for grading:** the PURE functions (`RangeEvaluator`, `ConflictDetector`) have zero external dependencies — no DB, no network, no LLM. That means 100% branch-coverage unit tests with no mocking gymnastics. This is exactly what a code reviewer wants to see.

---

## 4. Data Model (FHIR-shaped, provenance-aware)

```python
class Provenance(BaseModel):
    source: Literal["user_provided", "ai_extracted", "ai_generated"]
    confidence: Optional[float] = None      # only for ai_* sources
    document_id: Optional[str] = None       # which report this came from
    extracted_at: datetime
    edited_by: Optional[str] = None         # set if human-corrected
    edited_at: Optional[datetime] = None

class Observation(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_raw: Optional[str] = None         # fallback for non-numeric results
    unit: Optional[str] = None
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    reference_range_raw: Optional[str] = None   # as printed, e.g. "<5" or "8.6-10.2"
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
    age: Optional[int]
    sex: Optional[str]
    symptoms: List[str] = []
    conditions: List[str] = []
    allergies: List[str] = []
    medications: List[str] = []
    reports: List[DiagnosticReport] = []
    audit_log: List[dict] = []
```

Key design choices baked in:
- **Every extractable field is `Optional`** — the LLM must return `null` rather than invent a value. This is your "lossy parser, not a hallucination generator" story.
- **`reference_range_raw` is always stored alongside parsed low/high** — so a judge can see exactly what the report said vs. what your system parsed, and you can degrade gracefully when a range doesn't parse cleanly (e.g. `"<5"`, `">100"`, `"negative"`).
- **`flag` defaults to `UNKNOWN`**, never guessed, when a range is missing or unparseable — this directly satisfies "should not invent reference ranges."

---

## 5. The Core Pure Function — build and test this first

```python
def compare_to_range(
    value: Optional[float],
    range_low: Optional[float],
    range_high: Optional[float],
) -> Literal["LOW", "NORMAL", "HIGH", "UNKNOWN"]:
    if value is None or range_low is None or range_high is None:
        return "UNKNOWN"
    if value < range_low:
        return "LOW"
    if value > range_high:
        return "HIGH"
    return "NORMAL"
```

**Test cases to write (this is your test-suite backbone):**
- value below range → `LOW`
- value above range → `HIGH`
- value within range → `NORMAL`
- value exactly on the boundary (low) → `NORMAL` (define this explicitly, document the choice)
- value exactly on the boundary (high) → `NORMAL`
- missing value → `UNKNOWN`
- missing range_low or range_high → `UNKNOWN`
- range_low > range_high (malformed/reversed report data) → `UNKNOWN`, don't crash
- negative values (some tests can legitimately be negative, e.g. base excess) → still compares correctly
- non-numeric `value_raw` (e.g. "trace", "positive") → routed to `UNKNOWN`, never coerced

This function plus its test file is genuinely the single most important deliverable in the whole project for the "safety + code quality" part of your grade. Get it airtight before anything else.

Second pure function, same treatment:

```python
def detect_conflicts(
    patient_reported: dict,
    extracted_history: dict,
) -> List[Conflict]:
    """
    e.g. patient says "no known allergies" but a prior report
    lists an AllergyIntolerance — return a Conflict for UI flagging.
    Pure, deterministic, no LLM call.
    """
```

---

## 6. Build Order

1. **Data models** (Pydantic schemas above) — 100% of everything else depends on these being right
2. **`compare_to_range`** + full test suite — do this before touching any LLM code
3. **Patient intake form + validation** (frontend + API)
4. **LLM extraction service** — structured/schema-enforced output (native JSON schema or tool-calling mode of whichever model you use), validated against your Pydantic models before anything touches the DB
5. **Provenance tagging** — wrap every field write with source/confidence/timestamp
6. **Structured record view** in the UI (with source/AI badges)
7. **`detect_conflicts`** + tests
8. **Summary generation** — tightly constrained prompt (see §8), test that it never contains diagnosis-shaped language
9. **Human edit/verify UI** — edits update `provenance.edited_by/edited_at`, logged to `audit_log`
10. **FHIR-shaped export / PDF export**
11. *(Only if time remains)* bounding-box source highlighting

Do not start Tier 3 features until 1–9 are done, demo-able, and tested.

---

## 7. Suggested Stack

- **Backend:** FastAPI + Pydantic (validation and clean schemas come for free, reviewers like this)
- **LLM calls:** whichever model you have API access to, using its **native structured output / tool-calling / JSON-schema mode** — don't hand-parse free text JSON out of a prompt
- **DB:** SQLite for the hackathon (zero setup), SQLModel/SQLAlchemy as ORM
- **Frontend:** React, plain state (Context/hooks) — no need for Redux at this scale
- **Tests:** `pytest`, focused heavily on `compare_to_range` and `detect_conflicts`; a couple of integration tests for intake → structured record; mocked LLM responses for extraction-service tests (test *your* handling of good/bad LLM output, not the LLM itself)

---

## 8. Guardrails to Bake Into Prompts (Responsible AI)

For the **extraction** prompt:
- "Extract only what is explicitly present in the text. If a field is not present, return null. Do not infer, estimate, or calculate missing values."
- Enforce via schema/tool-calling, not just prompt wording.

For the **summary** prompt:
- "Summarize the patient's information in plain language. Do not provide a diagnosis, do not suggest a treatment, do not recommend medication changes, do not state or imply a medical conclusion. If something looks concerning, say 'this may be worth discussing with your doctor' rather than naming a condition."
- Write a small test that scans summary output for a blocklist of diagnostic/prescriptive phrasing patterns as a smoke test (not perfect, but shows judges you thought about it).

Also worth a line in your README:
- What data is sent to the LLM (minimum necessary) and what stays local
- That this is a hackathon prototype, not a HIPAA-compliant production system, and what you *would* add for that (BAA, encryption at rest, RBAC, audit-grade logging) — showing awareness without over-claiming compliance you can't actually deliver in the time given

---

## 9. What to Say in Your Pitch

Lead with the safety architecture, not the LLM. Judges see a lot of "we wrapped GPT in a chat UI" — the differentiator is:

> "Our LLM never makes a clinical judgment. It only extracts raw values into a strict schema. A separate, fully unit-tested, deterministic rule engine does every range comparison and conflict check — so a hallucination can produce a missing field, but it can never produce a wrong medical flag. Every field in the record is tagged with exactly where it came from, down to which document and whether a human edited it."

Then walk through the side-by-side source/structured view and the provenance badges live. That's your strongest 90 seconds.
