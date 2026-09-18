"""
Runs the analytical queries in queries/analytics.py and prints results,
demonstrating CTEs + window functions (NTILE, LAG, running SUM) against
the seeded e-commerce dataset.

Run: python run_analytics.py
"""
import sqlite3
from pathlib import Path

from queries import analytics

DB_PATH = Path(__file__).resolve().parent / "ecommerce.db"


def run(conn, title, sql, limit=10):
    print(f"\n=== {title} ===")
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    for i, row in enumerate(cur):
        if i >= limit:
            print(f"... ({limit}+ rows)")
            break
        print(" | ".join(str(v) for v in row))


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    run(conn, "Customer LTV ranking (top 10)", analytics.CUSTOMER_LTV_RANKING)
    run(conn, "Monthly category revenue (first 10 rows)", analytics.MONTHLY_CATEGORY_REVENUE)
    run(conn, "Order status mix by region", analytics.REGION_STATUS_MIX, limit=25)
    conn.close()
