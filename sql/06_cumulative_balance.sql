-- Business question: How does the running balance evolve over time?
-- Demonstrates: SUM() OVER unbounded preceding (cumulative)
WITH daily AS (
    SELECT
        date,
        SUM(amount) AS daily_net
    FROM transactions
    GROUP BY date
)
SELECT
    date,
    ROUND(daily_net, 2) AS daily_net,
    ROUND(
        SUM(daily_net) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
        2
    ) AS cumulative_balance
FROM daily
ORDER BY date;
