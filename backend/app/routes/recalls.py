"""Recall analytics endpoints for the FDA packaging recalls dashboard."""

from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/recalls", tags=["recalls"])

# ---------------------------------------------------------------------------
# Defect-pattern mapping used to unpack the "other" category
# ---------------------------------------------------------------------------
DEFECT_PATTERNS: dict[str, list[str]] = {
    "Mislabeling/Wrong Label": [
        "mislabel",
        "wrong label",
        "incorrect label",
        "label mix",
        "labeling error",
    ],
    "Contamination": [
        "contaminat",
        "foreign matter",
        "foreign substance",
        "impurit",
    ],
    "Potency Issues": [
        "potency",
        "strength",
        "concentration",
        "assay",
        "out of specification",
    ],
    "Manufacturing Defect": ["manufacturing", "production", "process", "batch"],
    "Stability/Degradation": ["stability", "degradation", "decomposition", "expir"],
    "Microbial/Sterility": ["microbial", "sterility", "bacterial", "endotoxin"],
    "Packaging Defect": ["packaging", "container", "closure", "seal", "blister"],
    "Documentation Error": [
        "documentation",
        "record",
        "certificate",
        "specification",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_df(db: Session) -> pd.DataFrame:
    """Load the recalls table into a pandas DataFrame and unpack 'other'."""
    df = pd.read_sql_query(text("SELECT * FROM recalls"), db.connection())
    df["recall_initiation_date"] = pd.to_datetime(df["recall_initiation_date"])
    df["recall_month"] = df["recall_initiation_date"].dt.to_period("M").astype(str)
    return _unpack_other(df)


def _unpack_other(df: pd.DataFrame) -> pd.DataFrame:
    """Re-classify rows whose primary_defect is 'other'."""
    df = df.copy()
    other_mask = df["primary_defect"] == "other"
    for idx in df.index[other_mask]:
        reason = str(df.at[idx, "reason_for_recall"]).lower()
        categorized = False
        for category, patterns in DEFECT_PATTERNS.items():
            if any(p in reason for p in patterns):
                df.at[idx, "primary_defect"] = category
                categorized = True
                break
        if not categorized:
            df.at[idx, "primary_defect"] = "Truly Other"
    return df


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Key performance indicators for the dashboard header."""
    df = _load_df(db)
    total = len(df)
    return {
        "total_recalls": total,
        "avg_cost_impact": round(float(df["estimated_cost_impact"].mean()), 2),
        "class_i_percent": round(
            float((df["classification_clean"] == "I").sum() / total * 100), 1
        ),
        "total_cost_impact": int(df["estimated_cost_impact"].sum()),
    }


@router.get("/classification")
def get_classification(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Classification distribution and cost box-plot data."""
    df = _load_df(db)

    # Distribution
    counts = df["classification_clean"].value_counts()
    total = len(df)
    distribution = [
        {
            "class": cls,
            "count": int(counts.get(cls, 0)),
            "percent": round(float(counts.get(cls, 0) / total * 100), 1),
        }
        for cls in ["I", "II", "III"]
    ]

    # Box-plot stats per class
    cost_by_class = []
    for cls in ["I", "II", "III"]:
        subset = df.loc[df["classification_clean"] == cls, "estimated_cost_impact"]
        if subset.empty:
            continue
        q1 = float(subset.quantile(0.25))
        q3 = float(subset.quantile(0.75))
        cost_by_class.append(
            {
                "class": cls,
                "min": float(subset.min()),
                "q1": round(q1, 2),
                "median": round(float(subset.median()), 2),
                "q3": round(q3, 2),
                "max": float(subset.max()),
            }
        )

    return {"distribution": distribution, "cost_by_class": cost_by_class}


@router.get("/defects")
def get_defects(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Top defects (with unpacked 'other') and risk-level distribution."""
    df = _load_df(db)

    defect_counts = df["primary_defect"].value_counts()
    top_defects = [
        {"defect": defect, "count": int(count)}
        for defect, count in defect_counts.head(12).items()
    ]

    risk_counts = df["risk_level"].value_counts()
    risk_levels = [
        {"level": level, "count": int(count)} for level, count in risk_counts.items()
    ]

    return {"top_defects": top_defects, "risk_levels": risk_levels}


@router.get("/timeline")
def get_timeline(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Monthly recall counts and annual breakdown by classification."""
    df = _load_df(db)

    # Monthly counts
    monthly = df.groupby("recall_month").size().reset_index(name="count")
    monthly = monthly.sort_values("recall_month")
    monthly_list = [
        {"month": row["recall_month"], "count": int(row["count"])}
        for _, row in monthly.iterrows()
    ]

    # Annual by classification
    yearly = (
        df.groupby(["recall_year", "classification_clean"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    annual_list = []
    for _, row in yearly.iterrows():
        entry: dict[str, Any] = {"year": int(row["recall_year"])}
        for cls in ["I", "II", "III"]:
            entry[f"class_{cls.lower()}"] = int(row.get(cls, 0))
        annual_list.append(entry)

    return {"monthly": monthly_list, "annual_by_class": annual_list}


@router.get("/insights")
def get_insights(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Business intelligence summary."""
    df = _load_df(db)

    total = len(df)
    defect_counts = df["primary_defect"].value_counts()
    top_defects = [
        {
            "defect": defect,
            "count": int(count),
            "percent": round(float(count / total * 100), 1),
        }
        for defect, count in defect_counts.head(5).items()
    ]

    cost_by_defect = (
        df.groupby("primary_defect")["estimated_cost_impact"]
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )
    cost_by_defect_list = [
        {"defect": defect, "avg_cost": round(float(avg), 2)}
        for defect, avg in cost_by_defect.items()
    ]

    labeling_count = int(
        df["primary_defect"].str.contains("label|Label", na=False).sum()
    )
    quality_count = int(
        df["primary_defect"]
        .str.contains("Contamination|Potency|Microbial|Sterility", na=False)
        .sum()
    )
    packaging_count = int(
        df["primary_defect"]
        .str.contains("Packaging|container|closure|moisture", na=False)
        .sum()
    )

    return {
        "total_recalls": total,
        "class_i_count": int((df["classification_clean"] == "I").sum()),
        "avg_resolution_days": round(float(df["days_to_resolution"].mean()), 1),
        "most_common_defect": str(defect_counts.index[0]),
        "total_cost_impact": int(df["estimated_cost_impact"].sum()),
        "top_defects": top_defects,
        "cost_by_defect": cost_by_defect_list,
        "labeling_count": labeling_count,
        "quality_count": quality_count,
        "packaging_count": packaging_count,
    }


@router.get("/table")
def get_table(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    classification: str | None = Query(None, alias="class"),
    defect: str | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    """Paginated recall records with optional filters."""
    df = _load_df(db)

    if classification:
        df = df[df["classification_clean"] == classification]
    if defect:
        df = df[df["primary_defect"] == defect]
    if year:
        df = df[df["recall_year"] == year]

    total = len(df)
    start = (page - 1) * limit
    page_df = df.iloc[start : start + limit]

    # Select a useful subset of columns for the table view
    columns = [
        "recall_number",
        "recalling_firm",
        "classification_clean",
        "primary_defect",
        "reason_for_recall",
        "recall_initiation_date",
        "risk_level",
        "estimated_cost_impact",
        "days_to_resolution",
        "state",
        "product_description",
    ]
    existing = [c for c in columns if c in page_df.columns]
    records = page_df[existing].copy()
    records["recall_initiation_date"] = records["recall_initiation_date"].astype(str)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "records": records.to_dict(orient="records"),
    }
