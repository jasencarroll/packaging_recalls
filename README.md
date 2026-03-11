# FDA Packaging Recall Analytics

A full-stack analytics dashboard that transforms raw FDA drug recall data into actionable insights. Built on the openFDA API, it processes 495 packaging-related recalls (2020-2024) through a data pipeline and presents them via an interactive dashboard with KPIs, classification breakdowns, defect analysis, and timeline trends.

**[Live Demo](https://packaging-recalls.jasencarroll.com)**

## Why This Exists

The FDA publishes drug recall data through the openFDA API, but the raw data is difficult to work with: inconsistent categorizations, no risk scoring, and no cost impact estimates. This project solves that by building a pipeline that extracts, cleans, and enriches the data, then serves it through a dashboard that makes patterns visible at a glance. Quality assurance teams, compliance officers, and anyone tracking pharmaceutical packaging safety can use it to spot trends, identify high-risk defect categories, and understand the financial impact of recalls.

## Dashboard Features

- **KPI Cards** -- total recalls, average cost impact, Class I critical percentage, total estimated cost impact
- **Classification Analysis** -- pie chart and bar chart breakdown of Class I / II / III recalls with cost distribution
- **Defect Analysis** -- top defect categories (with NLP-based reclassification of "other" entries), risk level distribution
- **Timeline Trends** -- monthly recall counts and annual classification breakdown
- **Insights Panel** -- business intelligence summary with top defects by frequency and cost
- **Data Table** -- paginated, filterable recall records

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, SQLAlchemy, PostgreSQL, Pandas |
| **Frontend** | React 19, Vite, Tailwind CSS v4, Recharts, shadcn/ui |
| **Data Pipeline** | Python scripts for openFDA API extraction, NLP categorization, risk scoring, cost modeling |
| **Tooling** | uv, Ruff (Python); Bun, Biome (TypeScript) |
| **CI** | GitHub Actions (backend lint, backend test, frontend lint, frontend build) |
| **Deployment** | Railway (multi-stage Dockerfile) |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js or [Bun](https://bun.sh/)
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL

### Installation

```bash
git clone https://github.com/jasencarroll/packaging_recalls.git
cd packaging_recalls
```

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
bun install
bun run dev          # Dev server on :5173, proxies /api to :8000
```

### Data Pipeline

```bash
# From the project root
uv sync
uv run python 1_data_pipeline/pipeline.py      # Fetch from openFDA API
uv run python 2_data_analysis/analysis.py      # Run analysis and generate visualizations
```

## Testing & Linting

```bash
# Backend
cd backend
uv run pytest -v
uv run ruff check .
uv run ruff format --check .

# Frontend
cd frontend
bun run lint
bun run build
```

## Project Structure

```
packaging_recalls/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, static file serving
│   │   ├── database.py          # SQLAlchemy engine and session
│   │   ├── config.py            # Settings (DATABASE_URL, etc.)
│   │   └── routes/
│   │       ├── recalls.py       # Analytics endpoints (KPIs, classification, defects, timeline)
│   │       └── health.py        # Health check
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/Dashboard.tsx
│   │   └── components/
│   │       ├── KPICard.tsx
│   │       ├── ClassificationCharts.tsx
│   │       ├── DefectCharts.tsx
│   │       ├── TimelineCharts.tsx
│   │       └── InsightsPanel.tsx
│   └── vite.config.ts
├── 1_data_pipeline/
│   ├── pipeline.py              # FDA API extraction and transformation
│   └── fda_recall_data/         # Raw and processed CSV/JSON output
├── 2_data_analysis/
│   ├── analysis.py              # Data cleaning, risk scoring, visualization generation
│   └── visualizations/          # Static PNG charts
├── Dockerfile                   # Multi-stage build (Bun + uv)
├── railway.json
├── pyproject.toml
└── uv.lock
```

## Deployment

Deployed on [Railway](https://railway.com/) using a multi-stage Dockerfile:

1. **Stage 1** -- Builds the React frontend with Bun
2. **Stage 2** -- Installs the FastAPI backend with uv, copies the built frontend, and serves everything as a single container

The production build serves the React SPA from FastAPI with a catch-all route for client-side routing. Health checks hit `/api/health`.

## License

MIT License -- see [LICENSE](LICENSE) for details.
