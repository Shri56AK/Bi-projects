# Realtime Business Alert Engine

A metric-monitoring service that evaluates SQL-aggregated thresholds on a
schedule and fires alerts through pluggable channels (console / webhook /
email) — the "critical business alerts that notify clients of important
events as they happen" piece of a BI stack, decoupled from any one
dashboarding tool.

## Stack
- **SQL**: SQLite schema in `db/schema.sql` — `metric_readings`,
  `alert_rules`, `alert_events`. The evaluator computes a rolling average
  over each rule's lookback window directly in SQL (`AVG(metric_value) ...
  WHERE recorded_at >= :since`) rather than pulling rows into Python.
- **Engine**: `alert_engine/monitor.py` — polls active rules, evaluates
  breaches, and dedupes so a sustained breach doesn't re-fire every cycle
  (a 10-minute cooldown checked via a second SQL query against
  `alert_events`).
- **Channels**: `alert_engine/notifiers.py` — console (always works),
  webhook (`ALERT_WEBHOOK_URL` env var), email (SMTP env vars). Falls back
  to a labelled dry-run print when unconfigured.
- **API**: FastAPI (`api/main.py`) — CRUD for alert rules, alert history,
  and metric history, meant to sit behind a React rule-management console.
- **Frontend**: React + Vite (`frontend/src/App.jsx`) — rule table with
  add/toggle/delete, recent fired-alert feed, and a metric history chart.

## Run it

```bash
# 1. Set up the DB (rules + 2h of synthetic metrics with an injected incident)
pip install -r requirements.txt
python db/setup.py

# 2. Start the management API
uvicorn api.main:app --reload --port 8001

# 3. Run the evaluator once to see it catch the injected incident
python -m alert_engine.monitor --once
# -> [ALERT] refund_rate_pct = 10.91 > 8.0  (rule #1)

# Or run it continuously:
python -m alert_engine.monitor

# 4. Frontend (new terminal)
cd frontend && npm install && npm run dev   # http://localhost:5174
```

## Design notes
- Threshold evaluation and dedupe both happen as SQL queries against
  indexed columns (`metric_name, recorded_at`), so the engine scales to
  many rules/metrics without scanning full tables in Python.
- Rules, not code, define what's monitored — adding a new alert is an API
  call, not a deploy.
