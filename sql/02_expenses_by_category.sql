-- Business question: What are the top expense categories and their share of total?
-- Demonstrates: CTE, window function (SUM OVER), ranking
WITH exp AS (
    SELECT
        category,
        SUM(ABS(amount)) AS total_expense,
        COUNT(*) AS txn_count
    FROM transactions
    WHERE amount < 0
    GROUP BY category
),
ranked AS (
    SELECT
        category,
        total_expense,
        txn_count,
        ROUND(total_expense * 1.0 / SUM(total_expense) OVER (), 4) AS share_of_total,
        RANK() OVER (ORDER BY total_expense DESC) AS rank_by_spend
    FROM exp
)
SELECT *
FROM ranked
ORDER BY rank_by_spend;
