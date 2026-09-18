-- Drop in dependency order (children before parents) so this script can be
-- re-run safely, e.g. via `python db/setup.py`, without leaving behind
-- duplicate seed rows or orphaned foreign keys.
DROP TABLE IF EXISTS alert_events;
DROP TABLE IF EXISTS alert_rules;
DROP TABLE IF EXISTS metric_readings;

-- Business metrics the engine watches (e.g. hourly order volume, refund rate).
CREATE TABLE IF NOT EXISTS metric_readings (
    reading_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name  TEXT NOT NULL,
    metric_value REAL NOT NULL,
    recorded_at  TEXT NOT NULL   -- ISO timestamp
);

CREATE INDEX IF NOT EXISTS idx_readings_metric_time
    ON metric_readings (metric_name, recorded_at);

-- User-defined alert rules: fire when a metric crosses a threshold.
CREATE TABLE IF NOT EXISTS alert_rules (
    rule_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name   TEXT NOT NULL,
    comparison    TEXT NOT NULL CHECK (comparison IN ('>', '<', '>=', '<=')),
    threshold     REAL NOT NULL,
    lookback_mins INTEGER NOT NULL DEFAULT 5,   -- evaluate avg over this window
    channel       TEXT NOT NULL DEFAULT 'console', -- console | webhook | email
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- History of alerts that actually fired (for dedupe + audit trail).
CREATE TABLE IF NOT EXISTS alert_events (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id      INTEGER NOT NULL REFERENCES alert_rules(rule_id),
    metric_name  TEXT NOT NULL,
    metric_value REAL NOT NULL,
    threshold    REAL NOT NULL,
    comparison   TEXT NOT NULL,
    fired_at     TEXT NOT NULL DEFAULT (datetime('now')),
    channel      TEXT NOT NULL,
    delivered    INTEGER NOT NULL DEFAULT 0
);
