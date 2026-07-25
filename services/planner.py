"""SALVA Smart Planner — planificador del hogar."""

from datetime import date, timedelta

import pandas as pd

from services.bookings import load_bookings
from services.data_store import PLANNER_TASKS_FILE, next_id, read_csv, write_csv
from services.goals import load_goals
from services.home_history import load_history
from services.predict import generate_recommendations

TASK_COLUMNS = [
    "id", "title", "reason", "priority_bucket", "estimated_cost",
    "recommended_date", "preparation_status", "related_goal_id",
    "source", "postponed_until", "created_at",
]

BUCKETS = ["Urgente", "Este mes", "Próximos 3 meses", "Más adelante"]


def load_tasks() -> pd.DataFrame:
    return read_csv(PLANNER_TASKS_FILE, TASK_COLUMNS)


def _bucket_from_priority(priority: str) -> str:
    return {"Alta": "Urgente", "Media": "Este mes", "Baja": "Próximos 3 meses"}.get(priority, "Más adelante")


def sync_from_predict_and_bookings() -> None:
    df = load_tasks()
    existing_titles = set(df["title"].tolist()) if not df.empty else set()
    new_rows = []

    for rec in generate_recommendations():
        if rec["title"] in existing_titles:
            continue
        new_rows.append({
            "id": next_id(pd.concat([df, pd.DataFrame(new_rows)]) if new_rows else df, "PL"),
            "title": rec["title"],
            "reason": rec["reason"],
            "priority_bucket": _bucket_from_priority(rec["priority"]),
            "estimated_cost": str((rec["cost_low"] + rec["cost_high"]) / 2),
            "recommended_date": rec["suggested_date"],
            "preparation_status": "Sin preparar",
            "related_goal_id": "",
            "source": rec["source"],
            "postponed_until": "",
            "created_at": date.today().isoformat(),
        })

    pending = load_bookings()
    if not pending.empty:
        status_col = pending.get("booking_status", pending.get("status", ""))
        pend = pending[status_col.isin(["Pendiente", "Confirmada", "En curso"]) | (status_col == "")]
        for _, b in pend.iterrows():
            title = f"Servicio pendiente: {b['service_type']}"
            if title not in existing_titles:
                new_rows.append({
                    "id": next_id(pd.concat([df, pd.DataFrame(new_rows)]) if new_rows else df, "PL"),
                    "title": title,
                    "reason": b.get("problem_description", "Reserva activa"),
                    "priority_bucket": "Urgente",
                    "estimated_cost": str(b.get("approved_price") or b.get("initial_price") or 0),
                    "recommended_date": b.get("preferred_date", date.today().isoformat()),
                    "preparation_status": "Reservado",
                    "related_goal_id": "",
                    "source": "Reserva SALVA",
                    "postponed_until": "",
                    "created_at": date.today().isoformat(),
                })

    if new_rows:
        write_csv(PLANNER_TASKS_FILE, pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True))


def add_manual_task(title: str, reason: str, bucket: str, cost: float, rec_date: str) -> dict:
    df = load_tasks()
    row = {
        "id": next_id(df, "PL"),
        "title": title,
        "reason": reason,
        "priority_bucket": bucket,
        "estimated_cost": str(cost),
        "recommended_date": rec_date,
        "preparation_status": "Sin preparar",
        "related_goal_id": "",
        "source": "Manual",
        "postponed_until": "",
        "created_at": date.today().isoformat(),
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_csv(PLANNER_TASKS_FILE, df)
    return row


def postpone_task(task_id: str, days: int = 30) -> dict | None:
    df = load_tasks()
    idx = df[df["id"] == task_id].index
    if idx.empty:
        return None
    until = (date.today() + timedelta(days=days)).isoformat()
    df.loc[idx, "postponed_until"] = until
    df.loc[idx, "priority_bucket"] = "Más adelante"
    write_csv(PLANNER_TASKS_FILE, df)
    return df.loc[idx[0]].to_dict()


def tasks_by_bucket() -> dict[str, pd.DataFrame]:
    sync_from_predict_and_bookings()
    df = load_tasks()
    if df.empty:
        return {b: pd.DataFrame() for b in BUCKETS}
    today = date.today().isoformat()
    active = df[(df["postponed_until"] == "") | (df["postponed_until"] <= today)]
    return {b: active[active["priority_bucket"] == b] for b in BUCKETS}


def link_goal_to_task(task_id: str, goal_id: str) -> None:
    df = load_tasks()
    idx = df[df["id"] == task_id].index
    if not idx.empty:
        df.loc[idx, "related_goal_id"] = goal_id
        goals = load_goals()
        g = goals[goals["id"] == goal_id]
        if not g.empty:
            df.loc[idx, "preparation_status"] = f"Ahorro: {g.iloc[0]['name']}"
        write_csv(PLANNER_TASKS_FILE, df)
