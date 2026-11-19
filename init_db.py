"""
init_db.py - creates the library_db database, tables and sample data
by executing schema.sql.   Usage:  python init_db.py
"""
from pathlib import Path

from db import get_connection


def split_statements(script: str):
    """Remove '--' comment lines and split on ';' (schema.sql has no procedures)."""
    lines = [l for l in script.splitlines() if not l.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def main():
    script = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    conn = get_connection(use_database=False)
    cur = conn.cursor()
    try:
        for stmt in split_statements(script):
            cur.execute(stmt)
        conn.commit()
        print("Database 'library_db' created and sample data inserted.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
