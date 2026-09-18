# SQL Analytics & Query Optimization Toolkit

A focused, dependency-free (stdlib only) project demonstrating the
"SQL-first analytics" and "query optimization" parts of a BI/data
engineering role directly: CTEs, window functions, index design, and
measured before/after query performance on a synthetic e-commerce dataset
(customers, orders, order_items, products).

## What's in here
- `generate_dataset.py` — builds a SQLite e-commerce schema and seeds it
  (default: 5k customers, 800 products, 200k orders, ~500k order items).
- `queries/analytics.py` — three analytical queries built on CTEs and
  window functions:
  - **Customer LTV ranking** — `NTILE(10)` to decile customers by lifetime value.
  - **Monthly category revenue** — `SUM() OVER (PARTITION BY ... ORDER BY month)`
    for a running total, plus `LAG()` for month-over-month growth %.
  - **Order status mix by region** — two-stage CTE (counts, then totals) to
    compute each status's share of regional order volume.
- `run_analytics.py` — runs and prints all three.
- `benchmark.py` — the optimization half:
  1. Times two realistic dashboard queries **before and after** adding
     indexes on `orders(customer_id)`, `orders(order_date)`, and
     `order_items(order_id)`, capturing `EXPLAIN QUERY PLAN` output for each.
  2. Rewrites a naive nested-correlated-subquery ranking query as a single
     CTE + `RANK() OVER (...)`, and times both.

## Run it

```bash
python generate_dataset.py --orders 200000
python run_analytics.py
python benchmark.py          # writes benchmark_report.md
```

## Sample results (60k-order run on this machine)
- Customer order lookup: **8.4 ms → 0.02 ms** after indexing `orders(customer_id)`
  and `order_items(order_id)` (SQL plan moves from a full table `SCAN` to
  indexed `SEARCH`).
- Correlated-subquery ranking → CTE + `RANK()` rewrite: **~8x faster**
  (1.64 ms → 0.21 ms) on the same 5 customers' order history.

Numbers scale with dataset size and hardware — re-run `benchmark.py` to
regenerate for your own environment; it's the *shape* of the improvement
(scan → index search, nested subqueries → single windowed pass) that's the
point, not the specific milliseconds.

## Why SQLite
Chosen for zero-setup portability. Every query here is standard SQL (CTEs,
window functions, index DDL) and ports to Postgres/MySQL with minimal
syntax changes — the main SQLite-specific bit is `EXPLAIN QUERY PLAN`'s
output format, which differs from Postgres's `EXPLAIN ANALYZE` but serves
the same purpose.
