# PRD — MedLens: AI-Powered Clinical Information Intelligence

**Status:** Draft v1
**Owner:** Hackathon team
**Related docs:** `ARCHITECTURE.md`

---

## 1. Problem Statement

Medical information is scattered across patient-reported history, prescriptions, lab reports, and prior records. Reviewing it is slow and error-prone because nothing is unified, and raw AI summarization alone isn't trustworthy — a user can't tell what came from them, what an AI inferred, or whether a lab value is actually abnormal.

**MedLens** collects patient information and processes medical reports into a structured, understandable, and reviewable patient record — with every field traceable to its source and every clinical flag computed deterministically, never invented by an AI.

---

## 2. Goals

| Goal | Non-goal |
|---|---|
| Structure fragmented patient + report data into one reviewable record | Providing diagnoses or treatment recommendations |
| Make every field's origin (user vs. AI) visible and auditable | Being a HIPAA-certified production system |
| Flag lab values against ranges *given in the source report only* | Inventing or looking up "normal" reference ranges |
| Give a plain-language, non-diagnostic summary | Replacing clinical judgment |
| Ship something a judge can verify is correct via tests | Maximizing feature count |

---

## 3. Target User

Primary: a patient or caregiver trying to make sense of their own scattered medical documents before a doctor's visit.
Secondary (implied by "reviewable"/"human verification" requirements): a clinician or reviewer who needs to quickly audit what the AI did and correct it.

---

## 4. Core Requirements (from problem statement — all mandatory)

### 4.1 Patient Information Intake
- Capture: age, sex, symptoms, existing conditions, allergies, medications, other relevant free-text notes
- Validate input (types, required fields, reasonable ranges e.g. age)
- All intake fields are tagged `source: user_provided`

### 4.2 Medical Report Processing
- Accept uploaded medical reports (PDF/image at minimum)
- Extract: test name, value, unit, reference range (as printed), date, observations/notes
- Handle missing/unparseable fields gracefully (`null`, never guessed)

### 4.3 Structured Medical Record
- Present data in structured fields/tables, not a single AI-generated paragraph
- Record must be organized per report and aggregated per patient

### 4.4 Reference-Range Awareness
- Compare each numeric result to the reference range **printed in that specific report**
- Output one of: `LOW`, `NORMAL`, `HIGH`, `UNKNOWN`
- **Hard constraint:** the system must never fabricate a reference range not present in the source document. If no range is present or it doesn't parse, the flag is `UNKNOWN`.

### 4.5 Source & Provenance
- Every field is tagged with one of: `user_provided`, `ai_extracted`, `ai_generated`
- AI-derived fields carry a confidence score and a link back to the source document
- Human edits are recorded (editor identity/timestamp) separately from original provenance

### 4.6 AI-Powered Summary
- Plain-language, patient-friendly summary of the available information
- **Hard constraint:** no diagnosis, no treatment recommendation, no medication dosage guidance, no definitive clinical claims. Uncertain findings are framed as "worth discussing with your doctor," not stated as fact.

---

## 5. Additional Features — Prioritized

Prioritization reflects effort vs. judge-visible value, not the order listed in the brief. See `ARCHITECTURE.md §2` for implementation scope of each.

**Committed (Tier 1):**
- Human verification/editing of extracted fields, with audit trail
- Confidence indicators on AI-extracted fields

**Committed if time allows (Tier 2):**
- Inconsistency/conflict detection (patient-reported vs. extracted history) — implemented as a deterministic comparison, not an LLM judgment call
- FHIR-*shaped* structured output (`DiagnosticReport` → `Observation`), without full terminology-code mapping
- PDF/JSON export
- Timeline/audit history view
- Search and filtering across reports

**Stretch (Tier 3, cut first if time is short):**
- Side-by-side source-document/structured-data view with bounding-box highlighting
- Comparison view of current vs. previous reports
- Multi-page table stitching for reports with layout-breaking tables
- Real LOINC/SNOMED semantic code mapping
- Authentication and role-based access control

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Safety** | No clinical decision (range flag, conflict detection) may be produced by an LLM call — deterministic code only, per `ARCHITECTURE.md §1` |
| **Trust/Transparency** | Every displayed field must indicate its provenance in the UI, not just in the data model |
| **Reliability** | Malformed/partial LLM output must not crash the pipeline or silently produce a wrong value — falls back to `null`/`UNKNOWN` |
| **Privacy** | No PHI in logs; minimum-necessary data sent to any external LLM API; document this explicitly since a hackathon build can't be truly HIPAA-compliant |
| **Code quality** | Layered architecture, typed models (Pydantic), input validation at every boundary, no bare exception swallowing |
| **Testability** | All clinical-logic functions (range comparison, conflict detection) must be pure and unit-testable with no mocking required |

---

## 7. Success Metrics (for demo/self-evaluation)

- **Extraction completeness:** % of fields on a sample report correctly populated or correctly left `null`
- **Range-flag correctness:** 100% agreement between `compare_to_range` output and manual calculation on test reports (this is enforced by unit tests, not spot-checked)
- **Zero forbidden language:** summary output never contains diagnostic/prescriptive phrasing (tested against a blocklist as a smoke test)
- **Provenance coverage:** 100% of displayed fields show a source tag in the UI
- **Test coverage:** full branch coverage on `compare_to_range` and `detect_conflicts`; integration test for the intake → structured record path

---

## 8. Assumptions & Constraints

- Hackathon timebox — scope is deliberately cut to Tier 1 first; Tier 2/3 are explicitly optional
- Access to one LLM API with structured-output/tool-calling support is assumed
- Demo reports are assumed to be reasonably clean single-document lab reports unless the team has verified test data includes multi-page tables
- Not claiming HIPAA compliance; documenting responsible-AI principles instead of implementing full regulatory infrastructure

---

## 9. Open Questions (resolve during build, don't block on these)

- Which document types must be supported for the demo — PDF only, or also scanned images / photos of paper reports?
- Is there a fixed set of judge-provided test reports, or should the team source its own sample data?
- Single-session demo vs. persistent multi-visit history — affects how much the "timeline" feature matters
