# Export Schema (dashboard-ready)

All files live under `data/exports/` after `make run`.

## transactions.parquet / transactions.csv

| Column             | Type     | Description                                      |
|--------------------|----------|--------------------------------------------------|
| transaction_id     | string   | Unique ID                                        |
| date               | datetime | Transaction date                                 |
| amount             | float64  | Signed EUR amount                                |
| currency           | string   | EUR                                              |
| category           | string   | Category                                         |
| counterparty       | string   | Counterparty                                     |
| account            | string   | Account                                          |
| description        | string   | Description                                      |
| type               | string   | income / expense                                 |
| is_near_duplicate  | bool     | Near-duplicate flag                              |
| year_month         | string   | YYYY-MM                                          |
| is_income          | bool     | amount > 0                                       |
| is_expense         | bool     | amount < 0                                       |
| anomaly_iqr        | bool     | Flagged by IQR method                            |
| anomaly_zscore     | bool     | Flagged by Z-score                               |
| is_anomaly         | bool     | Combined flag                                    |
| anomaly_reason     | string   | Semicolon-separated method tags                  |

## monthly_summary.parquet

| Column         | Type    | Description                          |
|----------------|---------|--------------------------------------|
| year_month     | string  | YYYY-MM                              |
| income         | float64 | Sum of positive amounts              |
| expenses       | float64 | Sum of negative amounts              |
| txn_count      | int     | Number of transactions               |
| net_cash_flow  | float64 | income + expenses                    |
| expense_ratio  | float64 | \|expenses\| / income                |
| net_lag1       | float64 | Previous month net (for MoM)         |
| net_lag12      | float64 | 12-month lag net (for YoY)           |
| mom_var        | float64 | Absolute MoM change                  |
| mom_var_pct    | float64 | Relative MoM change                  |
| yoy_var        | float64 | Absolute YoY change                  |
| yoy_var_pct    | float64 | Relative YoY change                  |

## category_summary.parquet

| Column    | Type    | Description                     |
|-----------|---------|---------------------------------|
| category  | string  | Category name (or "Other")      |
| total     | float64 | Absolute expense total          |
| txn_count | int     | Count                           |
| share     | float64 | Share of total expenses         |

## kpis.csv

Single-row file with: total_income, total_expenses, net_cash_flow, burn_rate, margin, runway_months, mom_variance_pct, current_balance.
