-- Business question: What is monthly income, expenses and net cash flow?
-- Demonstrates: CTE, aggregation, date formatting
WITH monthly AS (
    SELECT
        strftime('%Y-%m', date) AS year_month,
        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS income,
        SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) AS expenses,
        SUM(amount) AS net_cash_flow,
        COUNT(*) AS txn_count
    FROM transactions
    GROUP BY strftime('%Y-%m', date)
)
SELECT
    year_month,
    ROUND(income, 2) AS income,
    ROUND(expenses, 2) AS expenses,
    ROUND(net_cash_flow, 2) AS net_cash_flow,
    txn_count,
    ROUND(expenses / NULLIF(income, 0), 4) AS expense_ratio
FROM monthly
ORDER BY year_month;
