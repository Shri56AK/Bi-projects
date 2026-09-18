"""
Creates alerts.db from schema.sql and seeds it with:
 - a few sample alert rules
 - a rolling stream of synthetic metric readings (order_volume, refund_rate,
   avg_response_ms) for the last 2 hours, including a deliberate spike near
   the end so the engine has something real to fire on.
"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "alerts.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def build_schema(conn):
    conn.executescript(SCHEMA_PATH.read_text())


def seed_rules(conn):
    rules = [
        ("refund_rate_pct", ">", 8.0, 10, "console"),
        ("avg_response_ms", ">", 800, 5, "console"),
        ("order_volume", "<", 5, 15, "console"),
    ]
    conn.executemany(
        """INSERT INTO alert_rules (metric_name, comparison, threshold, lookback_mins, channel)
           VALUES (?, ?, ?, ?, ?)""",
        rules,
    )


def seed_readings(conn, minutes=120):
    start = datetime.now() - timedelta(minutes=minutes)
    rows = []
    for m in range(minutes):
        ts = (start + timedelta(minutes=m)).isoformat(timespec="seconds")

        order_volume = max(0, round(random.gauss(12, 3)))
        refund_rate = round(max(0, random.gauss(2.5, 1.0)), 2)
        response_ms = round(max(50, random.gauss(300, 60)), 1)

        # Inject a deliberate incident in the last 10 minutes so the demo
        # has a real breach to alert on.
        if m >= minutes - 10:
            refund_rate = round(random.uniform(9, 14), 2)
            response_ms = round(random.uniform(850, 1300), 1)

        for name, val in [
            ("order_volume", order_volume),
            ("refund_rate_pct", refund_rate),
            ("avg_response_ms", response_ms),
        ]:
            rows.append((name, val, ts))

    conn.executemany(
        "INSERT INTO metric_readings (metric_name, metric_value, recorded_at) VALUES (?, ?, ?)",
        rows,
    )


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    seed_rules(conn)
    seed_readings(conn)
    conn.commit()
    conn.close()
    print(f"Initialized {DB_PATH} with rules + 2h of synthetic metric readings.")
