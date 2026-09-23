"""Streamlit dashboard — Financial Operations Analytics (simulation)."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTS = PROJECT_ROOT / "data" / "exports"

st.set_page_config(
    page_title="Financial Operations Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colour palette — max 2 primary + 1 accent
PRIMARY = "#1f77b4"
SECONDARY = "#ff7f0e"
ACCENT = "#d62728"
BG = "#0e1117"


@st.cache_data
def load_exports() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    txn = pd.read_parquet(EXPORTS / "transactions.parquet")
    monthly = pd.read_parquet(EXPORTS / "monthly_summary.parquet")
    cats = pd.read_parquet(EXPORTS / "category_summary.parquet")
    kpis = pd.read_csv(EXPORTS / "kpis.csv").iloc[0].to_dict()
    return txn, monthly, cats, kpis


def main() -> None:
    st.title("Financial Operations Analytics")
    st.caption("Simulation — synthetic data · not a production banking system")

    try:
        txn, monthly, cats, kpis = load_exports()
    except FileNotFoundError:
        st.error("Exports not found. Run `make run` (or `python -m src.pipeline`) first.")
        st.stop()

    # ── KPI Header ──────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Income", f"{kpis.get('total_income', 0):,.0f} EUR")
    c2.metric("Total Expenses", f"{kpis.get('total_expenses', 0):,.0f} EUR")
    c3.metric("Net Cash Flow", f"{kpis.get('net_cash_flow', 0):,.0f} EUR")
    c4.metric("Burn Rate", f"{kpis.get('burn_rate', 0):,.0f} EUR/mo")
    runway = float(kpis.get("runway_months", 0) or 0)
    c5.metric("Runway", "inf" if not math.isfinite(runway) else f"{runway:.1f} mo")

    st.divider()

    # ── Time series ─────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.subheader("Monthly Income vs Expenses vs Net")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=monthly["year_month"], y=monthly["income"], name="Income", marker_color=PRIMARY
            )
        )
        fig.add_trace(
            go.Bar(
                x=monthly["year_month"],
                y=monthly["expenses"],
                name="Expenses",
                marker_color=SECONDARY,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=monthly["year_month"],
                y=monthly["net_cash_flow"],
                name="Net",
                mode="lines+markers",
                line={"color": "white", "width": 2},
            )
        )
        fig.update_layout(
            barmode="relative",
            xaxis_title="Month",
            yaxis_title="EUR",
            legend_title="",
            height=380,
            margin={"t": 30, "b": 40},
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Expenses by Category (Top 8 + Other)")
        fig2 = px.bar(
            cats,
            x="total",
            y="category",
            orientation="h",
            labels={"total": "Total Expense (EUR)", "category": ""},
            color_discrete_sequence=[PRIMARY],
        )
        fig2.update_layout(height=380, margin={"t": 30, "b": 40}, yaxis={"autorange": "reversed"})
        st.plotly_chart(fig2, use_container_width=True)

    # ── MoM variance ────────────────────────────────────────────
    st.subheader("Month-over-Month Net Cash Flow Variance")
    if "mom_var" in monthly.columns:
        mom = monthly.dropna(subset=["mom_var"]).copy()
        colors = [ACCENT if v < 0 else PRIMARY for v in mom["mom_var"]]
        fig3 = go.Figure(
            go.Bar(
                x=mom["year_month"],
                y=mom["mom_var"],
                marker_color=colors,
                name="MoM Δ",
            )
        )
        fig3.update_layout(
            xaxis_title="Month",
            yaxis_title="EUR change",
            height=320,
            margin={"t": 20, "b": 40},
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("MoM variance columns not present — re-run pipeline.")

    # ── Anomalies ───────────────────────────────────────────────
    st.subheader("Anomalous Transactions")
    anom = txn[txn.get("is_anomaly", False)].copy()
    if anom.empty:
        st.success("No anomalies flagged under current thresholds.")
    else:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.metric("Flagged", len(anom))
            scatter = px.scatter(
                anom,
                x="date",
                y="amount",
                color="category",
                hover_data=["transaction_id", "counterparty", "anomaly_reason"],
                title="Anomaly scatter (amount vs date)",
            )
            scatter.update_layout(height=300, margin={"t": 40})
            st.plotly_chart(scatter, use_container_width=True)
        with col_b:
            display_cols = [
                c
                for c in [
                    "date",
                    "transaction_id",
                    "category",
                    "counterparty",
                    "amount",
                    "anomaly_reason",
                ]
                if c in anom.columns
            ]
            st.dataframe(
                anom[display_cols].sort_values("amount").head(50),
                use_container_width=True,
                height=340,
            )

    # ── AI Commentary ───────────────────────────────────────────
    st.subheader("AI Commentary (latest period)")
    report_files = sorted((PROJECT_ROOT / "reports").glob("report_*.md"))
    if report_files:
        latest = report_files[-1].read_text(encoding="utf-8")
        # Extract commentary section
        if "## AI Commentary" in latest:
            comment = latest.split("## AI Commentary")[-1].split("---")[0].strip()
            st.info(comment)
        else:
            st.info(latest[:500])
    else:
        st.warning("No report generated yet. Run the pipeline.")

    st.divider()
    st.caption(
        "This is a simulation. No real banking API is connected. "
        "Data is synthetic. Built for portfolio demonstration."
    )


if __name__ == "__main__":
    main()
