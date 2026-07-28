"""SALVA Pay — pagos y simulación financiera."""

from datetime import datetime

import pandas as pd

from services.bookings import is_fully_paid, load_bookings
from services.formatting import format_ars
from services.goals import total_saved

INSTALLMENT_RATES = {1: 0.0, 3: 0.08, 6: 0.14, 12: 0.22}


def payment_summary() -> dict:
    df = load_bookings()
    if df.empty:
        return {
            "completed_total": 0, "pending_total": 0, "pending_count": 0,
            "completed_count": 0, "month_spent": 0,
        }
    prices = pd.to_numeric(df.get("approved_price", df.get("initial_price", 0)), errors="coerce").fillna(0)
    df = df.copy()
    df["_price"] = prices
    paid_mask = df.apply(lambda r: is_fully_paid(r.to_dict()), axis=1)
    paid = df[paid_mask]
    pending = df[~paid_mask]
    now_month = datetime.now().strftime("%Y-%m")
    month_paid = paid[paid["paid_at"].str.startswith(now_month, na=False)] if not paid.empty else paid
    return {
        "completed_total": float(paid["_price"].sum()) if not paid.empty else 0,
        "pending_total": float(pending["_price"].sum()) if not pending.empty else 0,
        "pending_count": len(pending),
        "completed_count": len(paid),
        "month_spent": float(month_paid["_price"].sum()) if not month_paid.empty else 0,
    }


def simulate_financing(amount: float, installments: int) -> dict:
    rate = INSTALLMENT_RATES.get(installments, 0.22)
    total = amount * (1 + rate)
    monthly = total / installments if installments else total
    return {
        "installments": installments,
        "monthly": monthly,
        "total": total,
        "rate_label": f"{int(rate * 100)}% simulado",
    }


def recent_transactions(limit: int = 5) -> pd.DataFrame:
    df = load_bookings()
    if df.empty:
        return df
    prices = pd.to_numeric(df.get("approved_price", df.get("initial_price", 0)), errors="coerce").fillna(0)
    df = df.copy()
    df["_price"] = prices
    sort_col = "created_at" if "created_at" in df.columns else "id"
    cols = ["id", "service_type", "professional_name", "payment_status", "paid_at", "_price"]
    return (
        df.sort_values(sort_col, ascending=False)
        .head(limit)[cols]
        .rename(columns={"_price": "amount"})
    )


def pay_dashboard_metrics() -> dict:
    s = payment_summary()
    return {
        "pagado": format_ars(s["completed_total"]),
        "pendiente": format_ars(s["pending_total"]),
        "mes": format_ars(s["month_spent"]),
        "ahorros_objetivos": format_ars(total_saved()),
    }
