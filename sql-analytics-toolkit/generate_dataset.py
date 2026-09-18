"""
Generates a realistic-scale e-commerce dataset (customers, orders,
order_items, products) into SQLite so the optimization demos have enough
rows for query plans and indexes to actually matter.

Run: python generate_dataset.py [--orders 200000]
"""
import sqlite3
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ecommerce.db"

CATEGORIES = ["Electronics", "Home", "Apparel", "Sports", "Books", "Toys", "Beauty"]
REGIONS = ["North", "South", "East", "West", "Central"]


def build_schema(conn):
    conn.executescript(
        """
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            region      TEXT NOT NULL,
            signup_date TEXT NOT NULL
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            category   TEXT NOT NULL,
            unit_price REAL NOT NULL
        );

        CREATE TABLE orders (
            order_id    INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
            order_date  TEXT NOT NULL,
            status      TEXT NOT NULL
        );

        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id      INTEGER NOT NULL REFERENCES orders(order_id),
            product_id    INTEGER NOT NULL REFERENCES products(product_id),
            quantity      INTEGER NOT NULL,
            line_total    REAL NOT NULL
        );
        """
    )


def seed(conn, n_customers=5000, n_products=800, n_orders=200000):
    today = datetime.today().date()

    conn.executemany(
        "INSERT INTO customers VALUES (?, ?, ?)",
        [
            (i, random.choice(REGIONS), (today - timedelta(days=random.randint(30, 1500))).isoformat())
            for i in range(1, n_customers + 1)
        ],
    )

    conn.executemany(
        "INSERT INTO products VALUES (?, ?, ?)",
        [
            (i, random.choice(CATEGORIES), round(random.uniform(5, 500), 2))
            for i in range(1, n_products + 1)
        ],
    )

    order_rows = []
    item_rows = []
    item_id = 1
    statuses = ["completed", "completed", "completed", "cancelled", "refunded"]

    for order_id in range(1, n_orders + 1):
        customer_id = random.randint(1, n_customers)
        order_date = (today - timedelta(days=random.randint(0, 365))).isoformat()
        status = random.choice(statuses)
        order_rows.append((order_id, customer_id, order_date, status))

        for _ in range(random.randint(1, 4)):
            product_id = random.randint(1, n_products)
            qty = random.randint(1, 5)
            # unit price unknown here without a join; approximate for line_total
            line_total = round(qty * random.uniform(5, 500), 2)
            item_rows.append((item_id, order_id, product_id, qty, line_total))
            item_id += 1

    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", order_rows)
    conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", item_rows)
    conn.commit()
    print(f"Seeded {n_customers} customers, {n_products} products, {n_orders} orders, {len(item_rows)} order_items.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=200000)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    seed(conn, n_orders=args.orders)
    conn.close()
