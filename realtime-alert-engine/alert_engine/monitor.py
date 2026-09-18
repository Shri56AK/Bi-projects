"""
Core evaluation loop: for each active rule, compute the metric's average
over its lookback window (SQL, not Python), compare against the threshold,
and fire + record an alert event if breached — deduped so the same breach
doesn't re-notify every poll cycle.

Run standalone:
    python -m alert_engine.monitor --once      # single evaluation pass
    python -m alert_engine.monitor              # polls every 30s
"""
import sqlite3
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

from . import notifiers

DB_PATH = Path(__file__).resolve().parent.parent / "alerts.db"

# Average of the metric over the rule's lookback window, computed in SQL.
METRIC_AVG_SQL = """
SELECT AVG(metric_value) AS avg_value, COUNT(*) AS n
FROM metric_readings
WHERE metric_name = :metric_name
  AND recorded_at >= :since;
"""

# Has this exact rule already fired in the last `cooldown_mins`? (dedupe)
RECENT_FIRE_SQL = """
SELECT COUNT(*) AS n
FROM alert_events
WHERE rule_id = :rule_id
  AND fired_at >= :since;
"""

INSERT_EVENT_SQL = """
INSERT INTO alert_events (rule_id, metric_name, metric_value, threshold, comparison, channel, delivered)
VALUES (:rule_id, :metric_name, :metric_value, :threshold, :comparison, :channel, 1);
"""

COMPARATORS = {
    ">": lambda v, t: v > t,
    "<": lambda v, t: v < t,
    ">=": lambda v, t: v >= t,
    "<=": lambda v, t: v <= t,
}

COOLDOWN_MINUTES = 10


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def evaluate_once(conn) -> list[dict]:
    conn.row_factory = _dict_factory
    rules = conn.execute("SELECT * FROM alert_rules WHERE is_active = 1").fetchall()
    fired = []

    for rule in rules:
        since = (datetime.now() - timedelta(minutes=rule["lookback_mins"])).isoformat(timespec="seconds")
        agg = conn.execute(METRIC_AVG_SQL, {"metric_name": rule["metric_name"], "since": since}).fetchone()

        if agg["avg_value"] is None:
            continue  # no data yet for this metric

        breached = COMPARATORS[rule["comparison"]](agg["avg_value"], rule["threshold"])
        if not breached:
            continue

        cooldown_since = (datetime.now() - timedelta(minutes=COOLDOWN_MINUTES)).isoformat(timespec="seconds")
        recent = conn.execute(RECENT_FIRE_SQL, {"rule_id": rule["rule_id"], "since": cooldown_since}).fetchone()
        if recent["n"] > 0:
            continue  # already alerted recently, don't spam

        alert = {
            "rule_id": rule["rule_id"],
            "metric_name": rule["metric_name"],
            "metric_value": round(agg["avg_value"], 2),
            "threshold": rule["threshold"],
            "comparison": rule["comparison"],
            "channel": rule["channel"],
        }
        notifiers.dispatch(rule["channel"], alert)
        conn.execute(INSERT_EVENT_SQL, alert)
        conn.commit()
        fired.append(alert)

    return fired


def run_forever(interval_seconds=30):
    conn = sqlite3.connect(DB_PATH)
    print(f"Alert engine started. Polling every {interval_seconds}s. Ctrl+C to stop.")
    try:
        while True:
            fired = evaluate_once(conn)
            if not fired:
                print(f"[{datetime.now().isoformat(timespec='seconds')}] no breaches.")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="evaluate a single pass and exit")
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()

    if args.once:
        conn = sqlite3.connect(DB_PATH)
        fired = evaluate_once(conn)
        conn.close()
        print(f"Evaluated all rules. {len(fired)} alert(s) fired.")
    else:
        run_forever(args.interval)
