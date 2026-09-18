"""
Management API for the alert engine: CRUD alert rules, view fired alert
history, and pull recent metric readings for the dashboard's chart.

Run:
    pip install -r requirements.txt
    python db/setup.py                      # one-time: creates alerts.db
    uvicorn api.main:app --reload --port 8001
"""
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = Path(__file__).resolve().parent.parent / "alerts.db"

app = FastAPI(title="Realtime Alert Engine API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    return conn


class RuleIn(BaseModel):
    metric_name: str
    comparison: str
    threshold: float
    lookback_mins: int = 5
    channel: str = "console"


@app.get("/api/rules")
def list_rules():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alert_rules ORDER BY rule_id DESC").fetchall()
    conn.close()
    return rows


@app.post("/api/rules")
def create_rule(rule: RuleIn):
    if rule.comparison not in (">", "<", ">=", "<="):
        raise HTTPException(400, "comparison must be one of > < >= <=")
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO alert_rules (metric_name, comparison, threshold, lookback_mins, channel)
           VALUES (?, ?, ?, ?, ?)""",
        (rule.metric_name, rule.comparison, rule.threshold, rule.lookback_mins, rule.channel),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM alert_rules WHERE rule_id = ?", (new_id,)).fetchone()
    conn.close()
    return row


@app.patch("/api/rules/{rule_id}/toggle")
def toggle_rule(rule_id: int):
    conn = get_conn()
    row = conn.execute("SELECT is_active FROM alert_rules WHERE rule_id = ?", (rule_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "rule not found")
    new_val = 0 if row["is_active"] else 1
    conn.execute("UPDATE alert_rules SET is_active = ? WHERE rule_id = ?", (new_val, rule_id))
    conn.commit()
    conn.close()
    return {"rule_id": rule_id, "is_active": new_val}


@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM alert_rules WHERE rule_id = ?", (rule_id,))
    conn.commit()
    conn.close()
    return {"deleted": rule_id}


@app.get("/api/events")
def list_events(limit: int = 50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM alert_events ORDER BY fired_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows


@app.get("/api/metrics/{metric_name}")
def metric_history(metric_name: str, minutes: int = 120):
    conn = get_conn()
    rows = conn.execute(
        """SELECT recorded_at, metric_value FROM metric_readings
           WHERE metric_name = ?
           ORDER BY recorded_at DESC LIMIT ?""",
        (metric_name, minutes),
    ).fetchall()
    conn.close()
    return list(reversed(rows))


@app.get("/api/metrics")
def distinct_metrics():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT metric_name FROM metric_readings").fetchall()
    conn.close()
    return [r["metric_name"] for r in rows]
