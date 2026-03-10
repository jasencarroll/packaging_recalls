# packaging_recalls

FDA packaging recalls data pipeline and analysis. Extracts recall data from the FDA API, runs analytics on 587 packaging-related recalls (2020-2024), and serves an interactive dashboard.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Development](#development)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [License](#license)

## Features

- **FDA API Pipeline** — automated extraction and transformation of recall data
- **Data Analysis** — risk scoring, NLP categorization, cost impact modeling, time-series trends
- **Visualizations** — correlation heatmaps, defect distributions, severity breakdowns, wordclouds
- **Interactive Dashboard** — Streamlit app with real-time filtering and KPIs
- **SQLite Storage** — persistent local database for processed recall data

## Tech Stack

- **Language:** Python 3.11+
- **Package Manager:** [uv](https://docs.astral.sh/uv/)
- **Data:** Pandas, Matplotlib, Seaborn, Plotly
- **NLP:** WordCloud
- **Dashboard:** Streamlit
- **Type Checking:** mypy with pandas-stubs
- **Data Source:** [FDA openFDA API](https://open.fda.gov/)

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

### Installation

```bash
git clone https://github.com/jasencarroll/packaging_recalls.git
cd packaging_recalls
uv sync
```

## Development

```bash
# Step 1: Run the data pipeline
uv run python 1_data_pipeline/pipeline.py

# Step 2: Run analysis
uv run python 2_data_analysis/analysis.py

# Step 3: Launch the dashboard
uv run streamlit run 3_data_dashboard/app.py
```

### Type Checking

```bash
uv run mypy .
```

## Project Structure

```
packaging_recalls/
├── 1_data_pipeline/
│   ├── pipeline.py                    # FDA API extraction and transformation
│   └── fda_recall_data/
│       ├── fda_packaging_recalls_processed.csv
│       └── recall_summary.json
├── 2_data_analysis/
│   ├── analysis.py                    # Analytics and risk scoring
│   ├── database.db                    # SQLite database
│   ├── recall_columns_info.json
│   ├── recall_columns_info_cleaned.json
│   └── visualizations/
│       ├── all_primary_defects_distribution.png
│       ├── correlation_heatmap.png
│       ├── cost_by_classification.png
│       ├── recall_overview.png
│       ├── recall_reasons_wordcloud.png
│       ├── severity_by_defect.png
│       └── time_series.png
├── 3_data_dashboard/
│   ├── app.py                         # Streamlit dashboard
│   └── README.md
├── pyproject.toml
├── uv.lock
├── railway.json
└── LICENSE
```

## Deployment

### Railway

```bash
railway init
railway up
```

The `railway.json` config handles the build and start commands automatically.

## License

MIT License - see [LICENSE](LICENSE) for details.
