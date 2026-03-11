"""One-time migration: copy recalls data from SQLite to PostgreSQL.

Usage:
    cd backend && uv run python scripts/migrate_data.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

SQLITE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "2_data_analysis" / "database.db"
)
PG_URL = "postgresql://localhost/packaging_recalls"


def main() -> None:
    # --- Read from SQLite ---
    sqlite_conn = sqlite3.connect(str(SQLITE_PATH))
    df = pd.read_sql_query("SELECT * FROM recalls", sqlite_conn)
    sqlite_conn.close()
    print(f"Read {len(df)} rows from SQLite ({SQLITE_PATH})")

    # --- Write to PostgreSQL ---
    pg_engine = create_engine(PG_URL)

    with pg_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS recalls"))
        conn.commit()

    # Let pandas create the table from the DataFrame dtypes
    df.to_sql("recalls", pg_engine, if_exists="replace", index=False)
    print(f"Wrote {len(df)} rows to PostgreSQL ({PG_URL})")

    # Verify
    with pg_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM recalls")).scalar()
    print(f"Verified: {count} rows in PostgreSQL recalls table")


if __name__ == "__main__":
    main()
