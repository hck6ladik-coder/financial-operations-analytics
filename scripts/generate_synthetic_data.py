#!/usr/bin/env python3
"""Generate realistic synthetic financial transactions for the portfolio project."""

from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

CATEGORIES = {
    "Salary": {"type": "income", "mean": 4500, "std": 200, "freq": 1},
    "Freelance": {"type": "income", "mean": 1200, "std": 400, "freq": 0.3},
    "Rent": {"type": "expense", "mean": -1400, "std": 0, "freq": 1},
    "Groceries": {"type": "expense", "mean": -85, "std": 25, "freq": 8},
    "Dining": {"type": "expense", "mean": -45, "std": 20, "freq": 6},
    "Transport": {"type": "expense", "mean": -35, "std": 15, "freq": 12},
    "Utilities": {"type": "expense", "mean": -180, "std": 30, "freq": 1},
    "Subscriptions": {"type": "expense", "mean": -25, "std": 5, "freq": 4},
    "Healthcare": {"type": "expense", "mean": -90, "std": 50, "freq": 0.8},
    "Entertainment": {"type": "expense", "mean": -60, "std": 30, "freq": 3},
    "Travel": {"type": "expense", "mean": -350, "std": 150, "freq": 0.4},
    "Shopping": {"type": "expense", "mean": -120, "std": 60, "freq": 2},
    "Insurance": {"type": "expense", "mean": -95, "std": 10, "freq": 1},
    "Investment": {"type": "expense", "mean": -500, "std": 100, "freq": 0.5},
}

COUNTERPARTIES = {
    "Salary": ["Acme Corp Payroll", "TechStart GmbH"],
    "Freelance": ["Client A", "Client B", "Upwork", "Toptal"],
    "Rent": ["City Properties Ltd"],
    "Groceries": ["Lidl", "Tesco", "Whole Foods", "Aldi", "Carrefour"],
    "Dining": ["Restaurant XYZ", "Cafe Central", "Pizza Place", "Sushi Bar"],
    "Transport": ["Uber", "City Transit", "Shell", "BP", "Train Co"],
    "Utilities": ["Electric Co", "Water Utility", "Gas Provider"],
    "Subscriptions": ["Netflix", "Spotify", "Adobe", "GitHub", "AWS"],
    "Healthcare": ["City Clinic", "Pharmacy Plus", "Dental Care"],
    "Entertainment": ["Cinema", "Concert Hall", "Streaming Extra"],
    "Travel": ["Airbnb", "Airline", "Booking.com", "Hotel Group"],
    "Shopping": ["Amazon", "Zara", "MediaMarkt", "IKEA"],
    "Insurance": ["SafeLife Insurance"],
    "Investment": ["Brokerage Account", "Crypto Exchange"],
}

ACCOUNTS = ["Checking-001", "Savings-002", "Credit-003"]


def generate_transactions(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    rows = []
    current = start_date
    txn_id = 10000

    while current <= end_date:
        for cat, meta in CATEGORIES.items():
            n = (
                max(1, int(np.random.poisson(max(0.1, meta["freq"]))))
                if meta["freq"] < 2
                else int(meta["freq"] * random.uniform(0.8, 1.2))
            )
            for _ in range(n):
                day = (
                    1
                    if cat in ("Salary", "Rent", "Utilities", "Insurance")
                    else random.randint(1, 28)
                )
                try:
                    dt = current.replace(day=min(day, 28))
                except ValueError:
                    dt = current.replace(day=28)
                if dt < start_date or dt > end_date:
                    continue
                amount = float(np.random.normal(meta["mean"], meta["std"]))
                amount = -abs(amount) if meta["type"] == "expense" else abs(amount)
                if random.random() < 0.018:
                    amount *= random.uniform(2.5, 4.5)
                rows.append(
                    {
                        "transaction_id": f"TXN-{txn_id}",
                        "date": dt.strftime("%Y-%m-%d"),
                        "amount": round(amount, 2),
                        "currency": "EUR",
                        "category": cat,
                        "counterparty": random.choice(COUNTERPARTIES[cat]),
                        "account": random.choice(ACCOUNTS),
                        "description": f"{cat} - {random.choice(COUNTERPARTIES[cat])}",
                        "type": meta["type"],
                    }
                )
                txn_id += 1

        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1, day=1)
        else:
            current = current.replace(month=current.month + 1, day=1)

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["date", "amount", "counterparty", "category"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    start = datetime(2023, 1, 1)
    end = datetime(2025, 8, 31)
    df = generate_transactions(start, end)
    out = Path("data/raw/transactions.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Generated {len(df)} transactions → {out}")
    print(df.head(8).to_string())
    print("\nCategory counts:\n", df["category"].value_counts().to_string())
    print(f"\nDate range: {df['date'].min()} → {df['date'].max()}")
    print(f"Total income:  {df[df['amount'] > 0]['amount'].sum():,.2f} EUR")
    print(f"Total expenses: {df[df['amount'] < 0]['amount'].sum():,.2f} EUR")
