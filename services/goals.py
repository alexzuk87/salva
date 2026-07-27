"""SALVA Objetivos — metas de ahorro."""

from datetime import datetime

import pandas as pd

from services.data_store import SAVINGS_GOALS_FILE, next_id, read_csv, write_csv

GOAL_COLUMNS = [
    "id", "name", "category", "target_amount", "saved_amount",
    "target_date", "monthly_contribution", "created_at", "status",
]


def load_goals() -> pd.DataFrame:
    return read_csv(SAVINGS_GOALS_FILE, GOAL_COLUMNS)


def create_goal(name: str, category: str, target: float, saved: float,
                target_date: str, monthly: float) -> dict:
    df = load_goals()
    row = {
        "id": next_id(df, "GO"),
        "name": name,
        "category": category,
        "target_amount": str(target),
        "saved_amount": str(saved),
        "target_date": target_date,
        "monthly_contribution": str(monthly),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "status": "Activo",
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_csv(SAVINGS_GOALS_FILE, df)
    return row


def add_savings(goal_id: str, amount: float) -> dict | None:
    df = load_goals()
    idx = df[df["id"] == goal_id].index
    if idx.empty:
        return None
    current = float(df.loc[idx, "saved_amount"].iloc[0] or 0)
    df.loc[idx, "saved_amount"] = str(current + amount)
    target = float(df.loc[idx, "target_amount"].iloc[0] or 0)
    if current + amount >= target:
        df.loc[idx, "status"] = "Completado"
    write_csv(SAVINGS_GOALS_FILE, df)
    return df.loc[idx[0]].to_dict()


def assign_from_ahorro(goal_id: str, amount: float) -> tuple[bool, str]:
    import streamlit as st
    from services.accounts import _record_tx, unassigned_savings

    if amount <= 0:
        return False, "Ingresá un monto válido."
    key = f"assign_{goal_id}_{amount}"
    if st.session_state.get(key):
        return False, "Esta asignación ya fue registrada."
    df = load_goals()
    idx = df[df["id"] == goal_id].index
    if idx.empty:
        return False, "Objetivo no encontrado."
    free = unassigned_savings()
    if free < amount:
        return False, (
            "Tu saldo libre en SALVA Ahorro no alcanza. "
            "Transferí dinero desde SALVA Cuenta."
        )
    _record_tx(
        "ahorro_no_asignado", "objetivo", "asignacion_objetivo", amount,
        "Asignación de ahorro no asignado a SALVA Objetivo", goal_id=goal_id,
    )
    current = float(df.loc[idx, "saved_amount"].iloc[0] or 0)
    df.loc[idx, "saved_amount"] = str(current + amount)
    target = float(df.loc[idx, "target_amount"].iloc[0] or 0)
    if current + amount >= target:
        df.loc[idx, "status"] = "Completado"
    write_csv(SAVINGS_GOALS_FILE, df)
    st.session_state[key] = True
    return True, ""


def use_goal_for_service(goal_id: str, amount: float) -> dict | None:
    df = load_goals()
    idx = df[df["id"] == goal_id].index
    if idx.empty:
        return None
    current = float(df.loc[idx, "saved_amount"].iloc[0] or 0)
    if current < amount:
        return None
    df.loc[idx, "saved_amount"] = str(current - amount)
    write_csv(SAVINGS_GOALS_FILE, df)
    return df.loc[idx[0]].to_dict()


def assigned_to_goals() -> float:
    df = load_goals()
    if df.empty:
        return 0.0
    return float(pd.to_numeric(df["saved_amount"], errors="coerce").fillna(0).sum())


def total_saved() -> float:
    return assigned_to_goals()


def primary_goal() -> dict | None:
    df = load_goals()
    active = df[df["status"] != "Completado"]
    if active.empty:
        return None
    active = active.copy()
    active["_pct"] = pd.to_numeric(active["saved_amount"], errors="coerce") / pd.to_numeric(
        active["target_amount"], errors="coerce"
    )
    return active.sort_values("_pct", ascending=False).iloc[0].to_dict()
