"""
Seeds a SQLite database with synthetic manufacturing production data:
machines, production runs (with output, defects, downtime) and shifts.

Run:  python seed_data.py
"""
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "manufacturing.db"

MACHINES = [
    ("M-101", "CNC Mill", "Line A"),
    ("M-102", "CNC Mill", "Line A"),
    ("M-103", "Injection Molder", "Line B"),
    ("M-104", "Injection Molder", "Line B"),
    ("M-105", "Assembly Robot", "Line C"),
    ("M-106", "Packaging Unit", "Line C"),
]

SHIFTS = ["Morning", "Afternoon", "Night"]

DOWNTIME_REASONS = [
    "Scheduled Maintenance",
    "Unplanned Breakdown",
    "Material Shortage",
    "Changeover",
    "Quality Hold",
    None,  # most runs have no downtime
]


def build_schema(conn):
    conn.executescript(
        """
        DROP TABLE IF EXISTS production_runs;
        DROP TABLE IF EXISTS machines;

        CREATE TABLE machines (
            machine_id   TEXT PRIMARY KEY,
            machine_type TEXT NOT NULL,
            line         TEXT NOT NULL
        );

        CREATE TABLE production_runs (
            run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id        TEXT NOT NULL REFERENCES machines(machine_id),
            shift             TEXT NOT NULL,
            run_date          TEXT NOT NULL,   -- ISO date
            planned_units     INTEGER NOT NULL,
            good_units        INTEGER NOT NULL,
            defective_units   INTEGER NOT NULL,
            downtime_minutes  INTEGER NOT NULL,
            downtime_reason   TEXT
        );

        CREATE INDEX idx_runs_machine_date ON production_runs(machine_id, run_date);
        CREATE INDEX idx_runs_date ON production_runs(run_date);
        """
    )


def seed(conn, days=90):
    conn.executemany(
        "INSERT INTO machines (machine_id, machine_type, line) VALUES (?, ?, ?)",
        MACHINES,
    )

    start = datetime.today().date() - timedelta(days=days)
    rows = []
    for d in range(days):
        run_date = (start + timedelta(days=d)).isoformat()
        for machine_id, mtype, line in MACHINES:
            for shift in SHIFTS:
                planned = random.randint(400, 900)
                # Introduce occasional bad days for Line B to make the
                # dashboard's alerting/filtering demo meaningful.
                bad_day = line == "Line B" and random.random() < 0.08
                defect_rate = random.uniform(0.10, 0.22) if bad_day else random.uniform(0.01, 0.06)
                defective = int(planned * defect_rate)
                good = planned - defective

                downtime_reason = random.choice(DOWNTIME_REASONS)
                if bad_day:
                    downtime_reason = downtime_reason or "Unplanned Breakdown"
                    downtime = random.randint(45, 150)
                elif downtime_reason:
                    downtime = random.randint(5, 40)
                else:
                    downtime = 0

                rows.append(
                    (machine_id, shift, run_date, planned, good, defective, downtime, downtime_reason)
                )

    conn.executemany(
        """INSERT INTO production_runs
           (machine_id, shift, run_date, planned_units, good_units,
            defective_units, downtime_minutes, downtime_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    print(f"Seeded {len(MACHINES)} machines and {len(rows)} production runs into {DB_PATH}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    seed(conn)
    conn.close()
