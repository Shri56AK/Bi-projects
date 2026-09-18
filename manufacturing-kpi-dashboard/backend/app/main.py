"""
Manufacturing KPI Dashboard API
--------------------------------
A small FastAPI service that exposes SQL-driven manufacturing KPIs
(yield, defect rate, downtime, machine rankings) for a React dashboard,
in the spirit of an Apache Superset-style BI backend.

Run:
    pip install -r requirements.txt
    python seed_data.py          # one-time: generates manufacturing.db
    uvicorn app.main:app --reload --port 8000
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from . import queries
from .db import run_query

app = FastAPI(title="Manufacturing KPI Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _date_params(start_date: Optional[str], end_date: Optional[str], line: str):
    end = end_date or date.today().isoformat()
    start = start_date or (date.today() - timedelta(days=30)).isoformat()
    return {"start_date": start, "end_date": end, "line": line}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/lines")
def lines():
    rows = run_query(queries.DISTINCT_LINES_SQL, {})
    return [r["line"] for r in rows]


@app.get("/api/kpis")
def kpi_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    line: str = Query("ALL"),
):
    params = _date_params(start_date, end_date, line)
    row = run_query(queries.KPI_SUMMARY_SQL, params)
    return row[0] if row else {}


@app.get("/api/trend")
def daily_trend(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    line: str = Query("ALL"),
):
    params = _date_params(start_date, end_date, line)
    return run_query(queries.DAILY_TREND_SQL, params)


@app.get("/api/machines/ranking")
def machine_ranking(start_date: Optional[str] = None, end_date: Optional[str] = None):
    params = _date_params(start_date, end_date, "ALL")
    return run_query(queries.MACHINE_RANKING_SQL, params)


@app.get("/api/downtime/breakdown")
def downtime_breakdown(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    line: str = Query("ALL"),
):
    params = _date_params(start_date, end_date, line)
    return run_query(queries.DOWNTIME_BREAKDOWN_SQL, params)
