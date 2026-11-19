"""
db.py - MySQL connectivity helpers.

Connection settings are read from environment variables (defaults shown):
    DB_HOST=localhost  DB_PORT=3306  DB_USER=root  DB_PASSWORD=""  DB_NAME=library_db
"""
import os
from contextlib import contextmanager

import mysql.connector
import pandas as pd

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "20042004"),
}
DB_NAME = os.getenv("DB_NAME", "library_db")


def get_connection(use_database: bool = True):
    """Open a new MySQL connection."""
    cfg = dict(DB_CONFIG)
    if use_database:
        cfg["database"] = DB_NAME
    return mysql.connector.connect(**cfg)


def run_query(sql: str, params=None) -> pd.DataFrame:
    """Run a SELECT and return the rows as a DataFrame."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        cur.close()
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


def run_scalar(sql: str, params=None):
    """Run a SELECT that returns a single value."""
    df = run_query(sql, params)
    return None if df.empty else df.iloc[0, 0]


def execute(sql: str, params=None) -> int:
    """Run an INSERT / UPDATE / DELETE, commit, and return affected row count."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        count = cur.rowcount
        cur.close()
        return count
    finally:
        conn.close()


@contextmanager
def transaction():
    """
    Context manager giving a dict-cursor inside a transaction.
    Commits on success, rolls back on any exception.

        with transaction() as cur:
            cur.execute(...)
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
