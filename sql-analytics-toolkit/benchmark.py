"""
Benchmarks a handful of realistic queries before and after adding indexes,
and compares a naive correlated-subquery pattern against its window-function
rewrite. Prints EXPLAIN QUERY PLAN output plus wall-clock timings, and
writes a markdown report to benchmark_report.md.

Run:
    python generate_dataset.py --orders 200000   # once
    python benchmark.py
"""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ecommerce.db"
REPORT_PATH = Path(__file__).resolve().parent / "benchmark_report.md"

# A query with no supporting index on orders(customer_id) / order_items(order_id)
# beyond the default rowid — realistic "slow dashboard filter" scenario.
CUSTOMER_ORDER_LOOKUP = """
SELECT o.order_id, o.order_date, o.status, SUM(oi.line_total) AS order_total
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.customer_id = ?
GROUP BY o.order_id, o.order_date, o.status
ORDER BY o.order_date DESC;
"""

DATE_RANGE_FILTER = """
SELECT status, COUNT(*) AS n
FROM orders
WHERE order_date BETWEEN ? AND ?
GROUP BY status;
"""

# Naive: correlated subquery computing each order's rank among that
# customer's orders by value (classic anti-pattern -> O(n) per row).
NAIVE_CUSTOMER_ORDER_RANK = """
SELECT
    o.order_id,
    o.customer_id,
    (SELECT SUM(oi.line_total) FROM order_items oi WHERE oi.order_id = o.order_id) AS order_total,
    (
        SELECT COUNT(*) + 1
        FROM orders o2
        WHERE o2.customer_id = o.customer_id
          AND (SELECT SUM(oi2.line_total) FROM order_items oi2 WHERE oi2.order_id = o2.order_id)
              > (SELECT SUM(oi3.line_total) FROM order_items oi3 WHERE oi3.order_id = o.order_id)
    ) AS rank_within_customer
FROM orders o
WHERE o.customer_id IN (1, 2, 3, 4, 5)
ORDER BY o.customer_id, rank_within_customer;
"""

# Optimized: single pass with a CTE + window function, no correlated subqueries.
OPTIMIZED_CUSTOMER_ORDER_RANK = """
WITH order_totals AS (
    SELECT o.order_id, o.customer_id, SUM(oi.line_total) AS order_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IN (1, 2, 3, 4, 5)
    GROUP BY o.order_id, o.customer_id
)
SELECT
    order_id,
    customer_id,
    order_total,
    RANK() OVER (PARTITION BY customer_id ORDER BY order_total DESC) AS rank_within_customer
FROM order_totals
ORDER BY customer_id, rank_within_customer;
"""


def timed(conn, sql, params=(), repeats=3):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        conn.execute(sql, params).fetchall()
        times.append(time.perf_counter() - start)
    return min(times)


def explain(conn, sql, params=()):
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return "\n".join(str(r) for r in rows)


def drop_indexes(conn):
    conn.executescript(
        """
        DROP INDEX IF EXISTS idx_orders_customer;
        DROP INDEX IF EXISTS idx_orders_date;
        DROP INDEX IF EXISTS idx_order_items_order;
        """
    )


def add_indexes(conn):
    conn.executescript(
        """
        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_orders_date ON orders(order_date);
        CREATE INDEX idx_order_items_order ON order_items(order_id);
        """
    )
    conn.execute("ANALYZE;")


def main():
    conn = sqlite3.connect(DB_PATH)
    report = ["# SQL Optimization Benchmark\n"]

    # --- 1. Index impact on point lookups / range scans ---------------
    drop_indexes(conn)
    report.append("## 1. Index impact\n")

    for label, sql, params in [
        ("Customer order lookup (customer_id = ?)", CUSTOMER_ORDER_LOOKUP, (42,)),
        ("Date-range order status counts", DATE_RANGE_FILTER, ("2026-01-01", "2026-03-31")),
    ]:
        before_time = timed(conn, sql, params)
        before_plan = explain(conn, sql, params)
        report.append(f"### {label}\n")
        report.append(f"**Without index** — {before_time*1000:.2f} ms\n```\n{before_plan}\n```\n")

    add_indexes(conn)

    for label, sql, params in [
        ("Customer order lookup (customer_id = ?)", CUSTOMER_ORDER_LOOKUP, (42,)),
        ("Date-range order status counts", DATE_RANGE_FILTER, ("2026-01-01", "2026-03-31")),
    ]:
        after_time = timed(conn, sql, params)
        after_plan = explain(conn, sql, params)
        report.append(f"**With index** — {after_time*1000:.2f} ms\n```\n{after_plan}\n```\n")

    # --- 2. Query rewrite: correlated subqueries vs window function ---
    report.append("## 2. Query rewrite: correlated subqueries -> window function\n")

    naive_time = timed(conn, NAIVE_CUSTOMER_ORDER_RANK, repeats=3)
    optimized_time = timed(conn, OPTIMIZED_CUSTOMER_ORDER_RANK, repeats=3)

    speedup = naive_time / optimized_time if optimized_time > 0 else float("inf")
    report.append(f"- Naive (nested correlated subqueries): {naive_time*1000:.2f} ms\n")
    report.append(f"- Optimized (CTE + `RANK() OVER (...)`): {optimized_time*1000:.2f} ms\n")
    report.append(f"- **Speedup: {speedup:.1f}x**\n")

    conn.close()

    REPORT_PATH.write_text("\n".join(report))
    print(f"Report written to {REPORT_PATH}")
    print("\n".join(report))


if __name__ == "__main__":
    main()
