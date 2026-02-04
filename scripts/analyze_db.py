#!/usr/bin/env python3
"""
Analyse the job search pipeline database: tables, columns, row counts, and sample data.

Usage:
  python scripts/analyze_db.py [path_to_db]
  # Default path: data/jobs.db (relative to project root)

Run from project root so data/jobs.db resolves correctly.
"""

import sqlite3
import sys
from pathlib import Path


def get_db_path() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    # Default: data/jobs.db from project root (script in scripts/)
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "data" / "jobs.db"


def analyze(db_path: Path) -> None:
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("Create it by running a search from the web app or the CLI pipeline.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=" * 60)
    print("DATABASE: " + str(db_path.resolve()))
    print("=" * 60)

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cur.fetchall()]

    if not tables:
        print("No tables found.")
        conn.close()
        return

    for table in tables:
        print(f"\n--- Table: {table} ---")

        cur.execute(f"PRAGMA table_info({table})")
        columns = cur.fetchall()
        col_names = [c[1] for c in columns]
        print("Columns:", ", ".join(col_names))

        cur.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cur.fetchone()[0]
        print(f"Rows: {count}")

        if count > 0:
            cur.execute(f"SELECT * FROM [{table}] LIMIT 3")
            rows = cur.fetchall()
            for i, row in enumerate(rows):
                d = dict(zip(col_names, row))
                # Truncate long text for display
                short = {}
                for k, v in d.items():
                    if v is None:
                        short[k] = None
                    elif isinstance(v, str) and len(v) > 60:
                        short[k] = v[:57] + "..."
                    else:
                        short[k] = v
                print(f"  Sample {i + 1}: {short}")

    conn.close()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    analyze(get_db_path())
