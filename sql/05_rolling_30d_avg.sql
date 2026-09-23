-- Business question: What is the rolling 30-record average of daily net cash flow?
-- Note: the window covers the 30 most recent days *with transactions* (rows),
--       not 30 calendar days.
-- Demonstrates: window frame AVG() OVER (... ROWS BETWEEN)
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
        AVG(daily_net) OVER (
            ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_30d_avg
FROM daily
ORDER BY date;
