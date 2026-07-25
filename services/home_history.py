"""Libreta digital del hogar."""

from datetime import datetime

import pandas as pd

from services.data_store import HOME_HISTORY_FILE, next_id, read_csv, write_csv
from services.formatting import format_ars

HISTORY_COLUMNS = [
    "id", "booking_id", "date", "neighborhood", "service_category",
    "reported_problem", "work_completed", "professional_name", "final_price",
    "rating", "guarantee_status", "notes",
]


def load_history() -> pd.DataFrame:
    return read_csv(HOME_HISTORY_FILE, HISTORY_COLUMNS)


def add_to_history(
    booking_id: str, neighborhood: str, service_category: str,
    reported_problem: str, work_completed: str, professional_name: str,
    final_price: float, rating: int, guarantee_status: str, notes: str = "",
) -> dict:
    df = load_history()
    if not df[df["booking_id"] == booking_id].empty:
        return df[df["booking_id"] == booking_id].iloc[0].to_dict()
    row = {
        "id": next_id(df, "LH"),
        "booking_id": booking_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "neighborhood": neighborhood,
        "service_category": service_category,
        "reported_problem": reported_problem,
        "work_completed": work_completed,
        "professional_name": professional_name,
        "final_price": str(final_price),
        "rating": str(rating),
        "guarantee_status": guarantee_status,
        "notes": notes,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_csv(HOME_HISTORY_FILE, df)
    return row


def filter_history(
    category: str | None = None, professional: str | None = None, date_from: str | None = None,
) -> pd.DataFrame:
    df = load_history()
    if df.empty:
        return df
    if category and category != "Todos":
        df = df[df["service_category"] == category]
    if professional and professional.strip():
        df = df[df["professional_name"].str.contains(professional, case=False, na=False)]
    if date_from:
        df = df[df["date"] >= date_from]
    return df.sort_values("date", ascending=False).reset_index(drop=True)


def history_summary() -> dict:
    df = load_history()
    if df.empty:
        return {"total": 0, "spent": format_ars(0), "top_category": "—", "last_date": "—"}
    prices = pd.to_numeric(df["final_price"], errors="coerce").fillna(0)
    top = df["service_category"].value_counts().index[0] if not df.empty else "—"
    return {
        "total": len(df),
        "spent": format_ars(prices.sum()),
        "top_category": top,
        "last_date": df["date"].max(),
    }
