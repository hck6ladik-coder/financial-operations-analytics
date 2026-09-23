-- Business question: Which transactions are anomalous by z-score within their category?
-- Demonstrates: CTE, JOIN, window aggregates (AVG/STDDEV), filter
WITH stats AS (
    SELECT
        category,
        AVG(amount) AS mu,
        -- SQLite has no STDDEV; approximate with sqrt of variance
        SQRT(AVG(amount * amount) - AVG(amount) * AVG(amount)) AS sigma,
        COUNT(*) AS n
    FROM transactions
    GROUP BY category
    HAVING COUNT(*) >= 5
),
scored AS (
    SELECT
        t.transaction_id,
        t.date,
        t.category,
        t.counterparty,
        t.amount,
        s.mu,
        s.sigma,
        CASE WHEN s.sigma > 0 THEN (t.amount - s.mu) / s.sigma ELSE 0 END AS zscore
    FROM transactions t
    INNER JOIN stats s ON t.category = s.category
)
SELECT
    transaction_id,
    date,
    category,
    counterparty,
    ROUND(amount, 2) AS amount,
    ROUND(zscore, 3) AS zscore
FROM scored
WHERE ABS(zscore) > 3
ORDER BY ABS(zscore) DESC;
