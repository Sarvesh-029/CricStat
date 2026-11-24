# CricStat — IPL Statistical Analytics Platform

> Every Run. Every Wicket. Every Statistic.

CricStat transforms IPL match data (sourced from CricAPI) into meaningful cricket
insights using Python, Pandas, NumPy, FastAPI, React, and TypeScript.

## Phase status (current)

This repository currently delivers **Phase 1–3**:

- Project scaffolding (backend + frontend)
- CricAPI integration service (auth, retries, pagination, rate-limit handling)
- Data processing pipeline (JSON → normalized DataFrames → CSV/SQLite)
- Statistical calculation engine (batting/bowling/team analytics) with unit tests
- FastAPI endpoints (dashboard, leaderboards, players, teams, matches, venues, seasons)
- React + Tailwind frontend shell (Overview, Leaderboards; other modules scaffolded)

Advanced modules (player comparison, venue/season deep analytics, charts) are
scheduled for Phases 4–6.

## Tech stack

- Backend: Python 3.10+, FastAPI, Pandas, NumPy, SQLAlchemy, Pydantic
- Database: SQLite (local dev) — PostgreSQL-ready via `DATABASE_URL`
- Frontend: React, TypeScript, Tailwind CSS, Recharts, Lucide
- Data source: CricAPI (https://www.cricapi.com/)

## Setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set CRICAPI_API_KEY
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### Ingest data

```bash
cd backend
python -m scripts.ingest --limit 20
```

This fetches IPL series/matches/scorecards from CricAPI and writes processed
CSVs under `data/processed/`. Re-run after adding your API key.

### Tests

```bash
cd backend
pytest -q
```

## Configuration

Environment variables (see `backend/.env.example`):

- `CRICAPI_BASE_URL` — CricAPI base URL
- `CRICAPI_API_KEY` — your API key (never commit)
- `DATABASE_URL` — SQLAlchemy URL (default SQLite)
- `CACHE_TTL_SECONDS` — cache TTL

## Data & calculation notes

- Batting average = runs / dismissals (not-outs excluded from denominator).
- Batting strike rate = (runs / balls) × 100.
- Bowling average = runs conceded / wickets.
- Bowling economy = (runs conceded / legal balls) × 6 (never decimal overs).
- Bowling strike rate = legal balls / wickets.
- Win % = wins / decided matches × 100 (no-results excluded).
- Boundary % = (4s×4 + 6s×6) / total runs × 100.
- Bowler wickets exclude run-outs, retired hurt, etc.
- Legal balls exclude wides and no-balls.
- Rate-based leaderboards apply minimum eligibility thresholds.
- CricAPI scorecards do not provide ball-by-ball delivery data, so dot-ball,
  phase (powerplay/middle/death) and maidens-derived metrics are marked
  unavailable rather than fabricated.

## Limitations

- CricAPI free tier is heavily rate-limited (~100 calls/day).
- Historical IPL coverage depends on CricAPI's series catalog.
- Player images / team logos are only shown when provided by the API.
- No fake statistics are generated; missing data is reported as unavailable.

## Project structure

See the master prompt / `backend/app` for module layout. Key folders:

- `backend/app/services` — API client, data processing, analytics
- `backend/app/routes` — FastAPI routers
- `backend/app/utils/stats.py` — pure statistical functions
- `backend/tests` — unit tests
- `notebooks` — analysis notebooks
- `frontend` — React + TypeScript app
- `data/raw`, `data/processed` — ingested data