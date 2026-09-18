# Golgix DI Engineer — Project Portfolio

Three small full-stack projects built to demonstrate the exact stack in
the Golgix DI Engineer JD: **SQL + React + BI/dashboards + Python**.

| Project | Focus | Stack |
|---|---|---|
| `manufacturing-kpi-dashboard/` | BI-style dashboard on manufacturing data (yield, defect rate, downtime, machine ranking) | SQL (CTEs, window functions) + FastAPI + React/Recharts |
| `realtime-alert-engine/` | Threshold-based alerting engine + rule management console | SQL + Python (polling engine, dedupe logic) + FastAPI + React |
| `sql-analytics-toolkit/` | Query optimization case study: indexing + correlated-subquery → window-function rewrite, with measured before/after timings | Pure SQL + Python (stdlib only) |

Each project has its own README with run instructions. All three were
built and test-run end-to-end (API responses, `EXPLAIN QUERY PLAN` output,
and `npm run build` for both frontends all verified) before being handed
over here.

## Quick start (any project)
```bash
cd <project-name>
# see that project's README.md for exact steps
```

## Suggested git workflow
```bash
git init
git add .
git commit -m "Initial commit: DI Engineer portfolio projects"
git remote add origin <your-repo-url>
git push -u origin main
```
Consider three separate repos instead of one, if you'd rather link each
individually on your resume/LinkedIn.
