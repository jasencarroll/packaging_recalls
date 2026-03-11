# Packaging Recalls

FDA packaging recalls data pipeline, analysis, and interactive dashboard as a full-stack web app powered by the openFDA API.

## Build & Development

### Backend (Python / FastAPI)
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest -v
uv run ruff check .
uv run ruff format .
```

### Frontend (React / Vite)
```bash
cd frontend
bun install
bun run dev          # Dev server on :5173, proxies /api to :8000
bun run build
bun run lint
```

### Data Pipeline & Analysis
```bash
uv sync                                        # Install root dependencies
uv run python 1_data_pipeline/pipeline.py      # Fetch from FDA API
uv run python 2_data_analysis/analysis.py      # Run analysis and generate visualizations
uv run mypy .                                  # Type check
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React 19 + Vite + Tailwind v4 + Recharts
- **Data Pipeline**: Python scripts for FDA API extraction and transformation
- **API**: All endpoints under `/api/`

## Key Directories

```
backend/
  app/main.py          # FastAPI app, CORS, static serving
  app/database.py      # SQLAlchemy database setup
  app/config.py        # Settings
  app/routes/recalls.py  # Recall data endpoints
  app/routes/health.py   # Health check
  tests/

frontend/
  src/App.tsx
  src/pages/Dashboard.tsx       # Main dashboard view
  src/components/               # KPICard, ClassificationCharts, DefectCharts, etc.

1_data_pipeline/
  pipeline.py                   # FDA API extraction and transformation (FDARecallPipeline)
  fda_recall_data/              # Raw and processed CSV/JSON output

2_data_analysis/
  analysis.py                   # Data cleaning, risk scoring, visualization generation
  database.db                   # Original SQLite data (migrated to PostgreSQL)
  visualizations/               # Static PNG charts
```
