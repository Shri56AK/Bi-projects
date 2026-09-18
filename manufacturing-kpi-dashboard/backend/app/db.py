import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent / "manufacturing.db"


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    try:
        yield conn
    finally:
        conn.close()


def run_query(sql: str, params: dict):
    """SQLite doesn't support named params with ':' directly via execute
    the way some drivers do positionally, so translate simple `:name`
    placeholders to sqlite3's supported `:name` syntax (already native)."""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()
