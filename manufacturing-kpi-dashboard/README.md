# Manufacturing KPI Dashboard

A small BI-style dashboard for manufacturing production data — SQL (CTEs +
window functions) on the backend, a FastAPI REST layer, and a React
(Recharts) frontend. Built as a stand-in for the kind of "raw data → visual
story" dashboards described in the DI Engineer role: filterable KPIs,
trend lines with rolling averages, and machine-level rankings.

## Stack
- **SQL**: SQLite schema (`production_runs`, `machines`), analytical
  queries in `backend/app/queries.py` using CTEs and window functions
  (`AVG() OVER (... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`, `RANK()`).
- **Backend**: FastAPI (`backend/app/main.py`) exposing `/api/kpis`,
  `/api/trend`, `/api/machines/ranking`, `/api/downtime/breakdown`.
- **Frontend**: React + Vite + Recharts (`frontend/src/App.jsx`) — line/date
  filters, KPI cards, a defect-rate trend chart with 7-day rolling average,
  a downtime-by-reason bar chart, and a ranked machine table.

## Run it

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python seed_data.py          # generates manufacturing.db with 90 days of synthetic data
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

## Why these SQL choices
- A **CTE** filters/joins runs to machines once, reused by every downstream
  aggregate — keeps the query readable and avoids repeating the join.
- A **window function** (`AVG() OVER`) computes a 7-day rolling defect rate
  without a self-join or app-side loop, so trend smoothing happens in the
  database, not in Python.
- `RANK() OVER (ORDER BY defect_rate_pct DESC)` surfaces the worst-performing
  machines directly from SQL, which is what a real alerting rule would key off.

## Notes
- SQLite is used for portability; queries are written in standard SQL and
  port to Postgres/MySQL with minimal changes (mainly placeholder syntax).
- `seed_data.py` deliberately injects a higher defect rate on ~8% of Line B
  runs so the dashboard's filtering and ranking have something to surface.
