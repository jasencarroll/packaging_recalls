"""Shared test fixtures: PostgreSQL test database with sample recall data."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app

SQLALCHEMY_TEST_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://localhost/packaging_recalls_test"
)
engine = create_engine(SQLALCHEMY_TEST_URL)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DDL matching the real recalls table (subset of columns used by endpoints)
_CREATE_TABLE = """
CREATE TABLE recalls (
    recall_number       TEXT,
    recalling_firm      TEXT,
    classification      TEXT,
    classification_clean TEXT,
    primary_defect      TEXT,
    reason_for_recall   TEXT,
    recall_initiation_date TEXT,
    risk_level          TEXT,
    estimated_cost_impact INTEGER,
    days_to_resolution  REAL,
    state               TEXT,
    product_description TEXT,
    recall_year         INTEGER,
    severity_score      INTEGER,
    risk_score          INTEGER,
    quantity_numeric     REAL,
    product_type        TEXT
)
"""

_SAMPLE_ROWS = [
    (
        "D-001-2024",
        "Acme Pharma",
        "Class I",
        "I",
        "labeling_error",
        "Mislabeled dosage strength on bottle label",
        "2024-01-15",
        "Critical",
        500000,
        30.0,
        "CA",
        "Aspirin 100mg tablets",
        2024,
        9,
        85,
        10000.0,
        "Drugs",
    ),
    (
        "D-002-2024",
        "Beta Labs",
        "Class II",
        "II",
        "container_closure",
        "Container closure system failed integrity test",
        "2024-03-20",
        "High",
        250000,
        45.0,
        "NY",
        "Ibuprofen 200mg capsules",
        2024,
        6,
        60,
        5000.0,
        "Drugs",
    ),
    (
        "D-003-2023",
        "Gamma Inc",
        "Class III",
        "III",
        "other",
        "Product found with contamination from foreign substance",
        "2023-06-10",
        "Medium",
        100000,
        20.0,
        "TX",
        "Vitamin D 1000IU softgels",
        2023,
        3,
        30,
        20000.0,
        "Drugs",
    ),
    (
        "D-004-2023",
        "Delta Corp",
        "Class II",
        "II",
        "other",
        "Manufacturing process deviation in batch 2023-A",
        "2023-09-05",
        "High",
        350000,
        60.0,
        "FL",
        "Metformin 500mg tablets",
        2023,
        7,
        70,
        15000.0,
        "Drugs",
    ),
    (
        "D-005-2024",
        "Epsilon Rx",
        "Class I",
        "I",
        "other",
        "Stability data shows early degradation under storage",
        "2024-07-01",
        "Critical",
        800000,
        15.0,
        "IL",
        "Amoxicillin 250mg suspension",
        2024,
        10,
        90,
        8000.0,
        "Drugs",
    ),
]


@pytest.fixture(autouse=True)
def _setup_db():
    """Create and populate the test database before each test."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS recalls"))
        conn.execute(text(_CREATE_TABLE))
        conn.execute(
            text(
                """
                INSERT INTO recalls (
                    recall_number, recalling_firm, classification,
                    classification_clean, primary_defect, reason_for_recall,
                    recall_initiation_date, risk_level, estimated_cost_impact,
                    days_to_resolution, state, product_description,
                    recall_year, severity_score, risk_score, quantity_numeric,
                    product_type
                ) VALUES (
                    :rn, :rf, :cl, :cc, :pd, :rr, :rid, :rl, :eci,
                    :dtr, :st, :pdesc, :ry, :ss, :rs, :qn, :pt
                )
                """
            ),
            [
                {
                    "rn": r[0],
                    "rf": r[1],
                    "cl": r[2],
                    "cc": r[3],
                    "pd": r[4],
                    "rr": r[5],
                    "rid": r[6],
                    "rl": r[7],
                    "eci": r[8],
                    "dtr": r[9],
                    "st": r[10],
                    "pdesc": r[11],
                    "ry": r[12],
                    "ss": r[13],
                    "rs": r[14],
                    "qn": r[15],
                    "pt": r[16],
                }
                for r in _SAMPLE_ROWS
            ],
        )
        conn.commit()
    yield


def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def client():
    """Return a TestClient wired to the test database."""
    return TestClient(app)
