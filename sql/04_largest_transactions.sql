-- Business question: What are the largest absolute transactions?
-- Demonstrates: RANK() / DENSE_RANK(), CTE
WITH ranked AS (
    SELECT
        transaction_id,
        date,
        category,
        counterparty,
        amount,
        RANK() OVER (ORDER BY ABS(amount) DESC) AS rank_abs,
        DENSE_RANK() OVER (PARTITION BY category ORDER BY ABS(amount) DESC) AS rank_in_category
    FROM transactions
)
SELECT
    rank_abs,
    rank_in_category,
    transaction_id,
    date,
    category,
    counterparty,
    ROUND(amount, 2) AS amount
FROM ranked
WHERE rank_abs <= 20
ORDER BY rank_abs;
