"""
Analytical SQL demonstrating CTEs, window functions, and running/rolling
aggregates against the e-commerce dataset — the kind of "uncover insights
from diverse datasets" work called out in the JD.
"""

# Top customers by lifetime value, with a percentile rank so you can see
# where each customer sits relative to the whole base.
CUSTOMER_LTV_RANKING = """
WITH customer_revenue AS (
    SELECT
        c.customer_id,
        c.region,
        SUM(oi.line_total) AS lifetime_value,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id AND o.status = 'completed'
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.region
)
SELECT
    customer_id,
    region,
    lifetime_value,
    order_count,
    ROUND(lifetime_value / order_count, 2) AS avg_order_value,
    NTILE(10) OVER (ORDER BY lifetime_value DESC) AS ltv_decile
FROM customer_revenue
ORDER BY lifetime_value DESC
LIMIT 50;
"""

# Monthly revenue by category with a running (cumulative) total and
# month-over-month growth — both computed via window functions.
MONTHLY_CATEGORY_REVENUE = """
WITH monthly AS (
    SELECT
        p.category,
        strftime('%Y-%m', o.order_date) AS month,
        SUM(oi.line_total) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id AND o.status = 'completed'
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.category, month
)
SELECT
    category,
    month,
    revenue,
    SUM(revenue) OVER (PARTITION BY category ORDER BY month) AS cumulative_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (PARTITION BY category ORDER BY month))
        / NULLIF(LAG(revenue) OVER (PARTITION BY category ORDER BY month), 0),
        1
    ) AS mom_growth_pct
FROM monthly
ORDER BY category, month;
"""

# Order status mix per region, using a CTE to pre-aggregate and a second
# pass to compute each status's share of that region's orders.
REGION_STATUS_MIX = """
WITH region_status_counts AS (
    SELECT
        c.region,
        o.status,
        COUNT(*) AS order_count
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    GROUP BY c.region, o.status
),
region_totals AS (
    SELECT region, SUM(order_count) AS total FROM region_status_counts GROUP BY region
)
SELECT
    rsc.region,
    rsc.status,
    rsc.order_count,
    ROUND(100.0 * rsc.order_count / rt.total, 1) AS pct_of_region
FROM region_status_counts rsc
JOIN region_totals rt ON rt.region = rsc.region
ORDER BY rsc.region, pct_of_region DESC;
"""
