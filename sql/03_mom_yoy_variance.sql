-- Business question: How does net cash flow change month-over-month and year-over-year?
-- Demonstrates: CTE + LAG() window function
WITH monthly AS (
    SELECT
        strftime('%Y-%m', date) AS year_month,
        SUM(amount) AS net_cash_flow
    FROM transactions
    GROUP BY strftime('%Y-%m', date)
),
with_lags AS (
    SELECT
        year_month,
        net_cash_flow,
        LAG(net_cash_flow, 1) OVER (ORDER BY year_month) AS prev_month,
        LAG(net_cash_flow, 12) OVER (ORDER BY year_month) AS prev_year
    FROM monthly
)
SELECT
    year_month,
    ROUND(net_cash_flow, 2) AS net_cash_flow,
    ROUND(prev_month, 2) AS prev_month,
    ROUND(net_cash_flow - prev_month, 2) AS mom_var,
    ROUND((net_cash_flow - prev_month) / NULLIF(ABS(prev_month), 0) * 100, 2) AS mom_var_pct,
    ROUND(prev_year, 2) AS prev_year,
    ROUND(net_cash_flow - prev_year, 2) AS yoy_var,
    ROUND((net_cash_flow - prev_year) / NULLIF(ABS(prev_year), 0) * 100, 2) AS yoy_var_pct
FROM with_lags
ORDER BY year_month;
