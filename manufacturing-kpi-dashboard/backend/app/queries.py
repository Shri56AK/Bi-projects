"""
All analytical SQL lives here, isolated from API/routing code.
Uses CTEs and window functions (per the JD's 'modern SQL features') to
compute OEE-style KPIs, defect-rate trends, and machine rankings.
"""

# ---------------------------------------------------------------------------
# Overall KPI summary for a date range (optionally filtered by line)
# ---------------------------------------------------------------------------
KPI_SUMMARY_SQL = """
WITH filtered AS (
    SELECT r.*, m.line, m.machine_type
    FROM production_runs r
    JOIN machines m ON m.machine_id = r.machine_id
    WHERE r.run_date BETWEEN :start_date AND :end_date
      AND (:line = 'ALL' OR m.line = :line)
)
SELECT
    SUM(planned_units)                                   AS planned_units,
    SUM(good_units)                                       AS good_units,
    SUM(defective_units)                                   AS defective_units,
    SUM(downtime_minutes)                                   AS downtime_minutes,
    ROUND(100.0 * SUM(good_units) / NULLIF(SUM(planned_units), 0), 2)   AS yield_pct,
    ROUND(100.0 * SUM(defective_units) / NULLIF(SUM(good_units) + SUM(defective_units), 0), 2) AS defect_rate_pct
FROM filtered;
"""

# ---------------------------------------------------------------------------
# Daily trend with a 7-day rolling average (window function) so the
# dashboard can plot both the raw signal and a smoothed trend line.
# ---------------------------------------------------------------------------
DAILY_TREND_SQL = """
WITH daily AS (
    SELECT
        r.run_date,
        SUM(r.good_units)                                    AS good_units,
        SUM(r.defective_units)                                 AS defective_units,
        SUM(r.downtime_minutes)                                  AS downtime_minutes
    FROM production_runs r
    JOIN machines m ON m.machine_id = r.machine_id
    WHERE r.run_date BETWEEN :start_date AND :end_date
      AND (:line = 'ALL' OR m.line = :line)
    GROUP BY r.run_date
)
SELECT
    run_date,
    good_units,
    defective_units,
    downtime_minutes,
    ROUND(100.0 * defective_units / NULLIF(good_units + defective_units, 0), 2) AS defect_rate_pct,
    ROUND(
        AVG(100.0 * defective_units / NULLIF(good_units + defective_units, 0))
        OVER (ORDER BY run_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),
        2
    ) AS defect_rate_7d_avg
FROM daily
ORDER BY run_date;
"""

# ---------------------------------------------------------------------------
# Per-machine ranking with RANK() window function - surfaces which
# machines are driving defects/downtime for the period.
# ---------------------------------------------------------------------------
MACHINE_RANKING_SQL = """
WITH per_machine AS (
    SELECT
        m.machine_id,
        m.machine_type,
        m.line,
        SUM(r.planned_units)                                   AS planned_units,
        SUM(r.good_units)                                       AS good_units,
        SUM(r.defective_units)                                    AS defective_units,
        SUM(r.downtime_minutes)                                     AS downtime_minutes,
        ROUND(100.0 * SUM(r.defective_units) / NULLIF(SUM(r.good_units) + SUM(r.defective_units), 0), 2) AS defect_rate_pct
    FROM production_runs r
    JOIN machines m ON m.machine_id = r.machine_id
    WHERE r.run_date BETWEEN :start_date AND :end_date
    GROUP BY m.machine_id, m.machine_type, m.line
)
SELECT
    *,
    RANK() OVER (ORDER BY defect_rate_pct DESC) AS defect_rate_rank,
    RANK() OVER (ORDER BY downtime_minutes DESC) AS downtime_rank
FROM per_machine
ORDER BY defect_rate_rank;
"""

# ---------------------------------------------------------------------------
# Downtime breakdown by reason
# ---------------------------------------------------------------------------
DOWNTIME_BREAKDOWN_SQL = """
SELECT
    COALESCE(downtime_reason, 'None') AS reason,
    SUM(downtime_minutes)              AS total_minutes,
    COUNT(*)                            AS occurrences
FROM production_runs r
JOIN machines m ON m.machine_id = r.machine_id
WHERE r.run_date BETWEEN :start_date AND :end_date
  AND (:line = 'ALL' OR m.line = :line)
  AND downtime_minutes > 0
GROUP BY reason
ORDER BY total_minutes DESC;
"""

DISTINCT_LINES_SQL = "SELECT DISTINCT line FROM machines ORDER BY line;"
