# MedLens — AI-Powered Clinical Information Intelligence

> **LLMs extract. Code decides.**

MedLens turns fragmented patient information — self-reported history, symptoms, prescriptions, and lab reports — into a single structured, reviewable patient record. Every field is traceable to its source, and every clinical flag is computed deterministically, never guessed by an AI.

> ⚠️ **Not a medical device.** MedLens organizes and summarizes information for review — it does not diagnose, prescribe, or recommend treatment.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Pydantic + SQLAlchemy |
| Database | SQLite |
| Frontend | React + TypeScript + Vite |
| Testing | pytest |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

copy .env.example .env         # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Run Tests

```bash
cd backend
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## Project Structure

```
MedLens/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI route handlers
│   │   ├── core/            # Config, settings
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── services/        # Business logic
│   │   ├── clinical/        # Pure deterministic functions (range eval, conflicts)
│   │   ├── extraction/      # Document parsing + LLM integration
│   │   ├── db/              # Database engine + session
│   │   ├── utils/           # Shared utilities
│   │   └── main.py          # FastAPI app entry point
│   └── tests/
│       ├── unit/            # Pure function + endpoint tests
│       ├── services/        # Service layer tests (mocked deps)
│       └── integration/     # End-to-end pipeline tests
├── frontend/                # React + TypeScript + Vite
├── sample_data/             # Test lab reports
└── docs/                    # Architecture & PRD docs
```

---

## Safety & Responsible AI

- Reference ranges are **never invented** — if a report doesn't provide a parseable range, the flag is `UNKNOWN`
- Summary generation is constrained against diagnostic/treatment language
- No PHI in logs; minimum-necessary data sent to LLM
- This is a hackathon prototype, not HIPAA-compliant

---

## Architecture

See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) and [PRD.md](./docs/PRD.md) for full design docs.
