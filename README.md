# Financial Operations Analytics

**End-to-end project demonstrating SQL, Python, financial analysis, BI, and process automation on simulated financial data.**

A visitor can understand the full flow — data → analysis → automation → dashboard → practical output — in under 3 minutes.

> **This is a simulation. No real banking API is connected. Files are synthetic.**

---

## Dashboard Preview

*Run `make run && make dashboard` to generate live view. Screenshot placeholder — see [docs/dashboard.png.placeholder](docs/dashboard.png.placeholder).*

---

## Flow Diagram

```
Business Problem
      ↓
Raw Financial Data          (data/raw/)
      ↓
Data Cleaning & Validation  (src/clean.py, src/validate.py)
      ↓
SQL Analysis                (sql/*.sql — CTEs, windows, LAG, RANK)
      ↓
Python Analytics & Anomaly Detection  (src/kpis.py, src/anomaly.py)
      ↓
BI Dashboard                (dashboard/app.py — Streamlit + Plotly)
      ↓
Automated Reporting + AI Commentary   (src/report.py, ai/summarize.py)
      ↓
Business Insights
```

---

## Key Insights (from sample run)

- Cumulative net cash flow is strongly positive (~123 k EUR over ~32 months) driven by stable salary + freelance income.
- Top expense categories: Transport, Groceries, Dining — together >50 % of outflow.
- Trailing 3-month burn rate is low/zero in surplus months; runway remains comfortable.
- A small set of high-value outliers (Travel, Investment spikes) are correctly flagged by both IQR and Z-score.
- Month-over-month net variance stays within ±25 % most periods; larger swings trigger the alert gate.

---

## Quickstart

```bash
git clone <this-repo>
cd financial-operations-analytics
make setup          # installs dependencies
make run            # full pipeline < 1 min on sample data
make dashboard      # opens Streamlit at localhost:8501
make test           # pytest
```

One-command reproduction: `make setup && make run`

---

## Business Problem & Context

Finance teams need a repeatable way to turn raw transaction feeds into:

1. Trusted monthly cash-flow and category views,
2. Early warning on anomalous spend,
3. A short narrative a controller can read in 30 seconds.

This repository simulates that workflow end-to-end with clear layer separation so a hiring manager can evaluate applied SQL, typed Python, BI design, automation, and purposeful AI in minutes.

---

## Dataset

| Item        | Detail                                      |
|-------------|---------------------------------------------|
| Source      | Synthetic generator (`scripts/generate_synthetic_data.py`) |
| License     | Free for any use (generated for this repo)  |
| Size        | ~1.3 k rows, < 1 MB                         |
| Period      | 2023-01 → 2025-08                           |
| Currency    | EUR (signed amounts: expenses negative)     |
| How to obtain | Already committed under `data/raw/transactions.csv`. Re-generate with `python scripts/generate_synthetic_data.py`. |

See [docs/data_model.md](docs/data_model.md) for full column dictionary and cleaning rules.

---

## Architecture & Tech Stack

| Layer        | Choice                          | Why                                      |
|--------------|---------------------------------|------------------------------------------|
| Language     | Python 3.10+                    | Typed, ecosystem, reproducibility        |
| Storage      | Parquet + CSV                   | Zero-friction, portable                  |
| Validation   | Pandera schema contracts        | Fail-fast, documented                    |
| Analytics    | Pandas + pure SQL window funcs  | Transparent KPI formulas                 |
| Anomaly      | IQR + Z-score                   | Interpretable first                       |
| Dashboard    | Streamlit + Plotly              | Free, code-defined, git-friendly         |
| AI           | Structured dict → ≤120-word comment | Purposeful, no raw PII, deterministic fallback |
| Automation   | CLI (`python -m src.pipeline`)  | Simple; optional Prefect flow             |
| CI           | GitHub Actions (ruff + mypy + pytest) | Green on every PR                     |

---

## Repository Structure

```
financial-operations-analytics/
├── data/
│   ├── raw/              # Immutable source CSV
│   ├── interim/          # Intermediate (unused in minimal flow)
│   ├── processed/        # Cleaned Parquet
│   ├── exports/          # Dashboard-ready datasets
│   └── incoming/         # Drop zone for daily automation scenario
├── notebooks/            # EDA (optional exploratory)
├── sql/                  # One business question per .sql file
├── src/                  # Typed pipeline package
│   ├── ingest.py
│   ├── clean.py
│   ├── validate.py
│   ├── transform.py
│   ├── kpis.py
│   ├── anomaly.py
│   ├── export.py
│   ├── report.py
│   └── pipeline.py       # Orchestrator
├── dashboard/app.py      # Streamlit app
├── ai/summarize.py       # Structured → commentary
├── flows/                # Optional Prefect flow
├── reports/              # Generated MD + alerts/
├── docs/                 # data_model, schema, dashboard.png
├── tests/                # pytest (unit + pipeline E2E)
├── config.yaml           # All paths & thresholds
├── Makefile
├── requirements.txt
├── pyproject.toml
└── .github/workflows/ci.yml
```

---

## How to Run

```bash
make setup      # pip install -r requirements.txt
make run        # python -m src.pipeline
make test       # pytest
make lint       # ruff
make typecheck  # mypy
make dashboard  # streamlit run dashboard/app.py
```

Daily automation simulation:

```bash
# Drop a new file into data/incoming/ then:
python -m src.pipeline --source data/incoming/new_transactions.csv --date 2025-09-01
```

If anomaly count > threshold or MoM net deviation > 25 %, an alert JSON is written to `reports/alerts/`.

---

## KPI Definitions

| KPI               | Formula                                              |
|-------------------|------------------------------------------------------|
| Cash flow         | inflow − outflow (per period)                        |
| Burn rate         | avg monthly net outflow (trailing 3 months, abs)     |
| Margin            | (inflow − outflow) / inflow                          |
| Expense ratio     | \|expenses\| / income (by category or total)         |
| Runway months     | current_balance / burn_rate                          |
| MoM variance %    | (current − previous) / \|previous\|                  |

All formulas are implemented in `src/kpis.py` and mirrored in SQL where relevant.

---

## SQL Highlights

Every file under `sql/` has a header stating the business question and uses CTEs + window functions:

- `01_monthly_cashflow.sql` — income / expenses / net
- `02_expenses_by_category.sql` — top-N + share (`SUM() OVER`, `RANK()`)
- `03_mom_yoy_variance.sql` — `LAG(1)`, `LAG(12)`
- `04_largest_transactions.sql` — `RANK()` / `DENSE_RANK()`
- `05_rolling_30d_avg.sql` — `AVG() OVER (ROWS BETWEEN 29 PRECEDING …)`
- `06_cumulative_balance.sql` — `SUM() OVER (UNBOUNDED PRECEDING)`
- `07_anomalous_zscore.sql` — category-level z-score via JOIN + filter

Load the processed Parquet into SQLite (or any engine) and execute.

---

## Anomaly Detection

1. **IQR (default)** — flag outside `[Q1 − 1.5·IQR, Q3 + 1.5·IQR]` per category.
2. **Z-score** — `|z| > 3` per category.
3. Combined `is_anomaly` flag + reason string.

Thresholds live in `config.yaml`. Isolation Forest is intentionally left as an optional extension (documented in code comments) because univariate methods already surface the meaningful outliers on this dataset.

---

## AI Layer

**Contract** (`ai/summarize.py`):

- **Input**: structured dict `{kpis, top_categories, n_anomalies}`
- **Output**: string ≤ 120 words
- **Fallback**: deterministic template (always available, no external API)

> The AI layer converts analytical check results into a short comment for a financial specialist. It is optional and runs on structured summaries — never on raw PII.

Example output (deterministic fallback):

> Over the analysed period, total income reached 275,578 EUR against expenses of −152,433 EUR, producing a net cash flow of 123,145 EUR (margin 44.7 %). Month-over-month net cash flow improved by 3.2 %. The trailing burn rate sits at 0 EUR per month, implying roughly ∞ months of runway at the current balance. Largest expense shares: Transport (24 %), Groceries (16 %), Dining (11 %). 12 transactions were flagged as anomalous and warrant review.

---

## Automation Scenario

Every morning a new transactions file can land in `data/incoming/`. The CLI:

```bash
python -m src.pipeline --date YYYY-MM-DD --source data/incoming/file.csv
```

1. Ingests & validates schema/ranges (Pandera + range contracts).
2. Updates processed tables and exports.
3. Writes report + alert JSON if thresholds breached.
4. Prints a clear console message.

**Disclaimer (repeated):** This is a simulation. No real banking API is connected. Files are synthetic or public.

---

## What I Would Do Differently in a Real Banking Environment

1. Role-based access control and least-privilege service accounts.
2. Immutable audit trail for every data mutation.
3. Schema contracts, data-quality SLAs, and pipeline circuit breakers.
4. GDPR / data privacy: PII minimisation, tokenisation, retention policy.
5. Monitoring, alerting, and on-call runbooks for pipeline failures.
6. Idempotent jobs, retries with backoff, dead-letter queues.
7. Secrets management (Vault / cloud KMS) — no secrets in repo.
8. Full reproducibility: Docker images, dataset versioning (DVC), pinned deps.
9. Change management: PR reviews, CI gates, staging environment.
10. Reconciliation against source-of-truth ledgers before publishing reports.
11. Multi-currency FX rates with audit of conversion timestamps.
12. Separation of duties between data engineers, analysts, and report publishers.

---

## Roadmap / Next Steps

- [ ] Optional Prefect / Airflow DAG under `flows/`
- [ ] Docker Compose with PostgreSQL for the SQL layer
- [ ] Power BI `.pbix` variant (screenshot + file)
- [ ] Isolation Forest multivariate path behind a config flag
- [ ] Lightweight category classifier (description → category) with confidence
- [ ] Historical snapshot tables for point-in-time reporting

---

## License & Disclaimer

MIT License — see [LICENSE](LICENSE).

**This repository is a portfolio simulation.** It does not connect to any real bank, payment processor, or customer data. All figures are generated synthetically for demonstration of analytical engineering skills.
