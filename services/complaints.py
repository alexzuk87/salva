"""Reclamos de garantía SALVA."""

from datetime import datetime

import pandas as pd

from services.data_store import COMPLAINTS_FILE, next_id, read_csv, write_csv

COMPLAINT_COLUMNS = [
    "id", "booking_id", "category", "description", "evidence_note",
    "requested_resolution", "status", "created_at",
]

CATEGORIES = [
    "Trabajo incompleto", "Problema posterior al servicio", "Diferencia de precio",
    "Incumplimiento del horario", "Conducta del profesional", "Otro",
]

STATUSES = [
    "Reclamo iniciado", "En revisión", "Información adicional requerida",
    "Resolución propuesta", "Reclamo cerrado",
]


def load_complaints() -> pd.DataFrame:
    return read_csv(COMPLAINTS_FILE, COMPLAINT_COLUMNS)


def create_complaint(
    booking_id: str, category: str, description: str,
    requested_resolution: str, evidence_note: str = "",
) -> dict:
    df = load_complaints()
    row = {
        "id": next_id(df, "RC"),
        "booking_id": booking_id,
        "category": category,
        "description": description,
        "evidence_note": evidence_note,
        "requested_resolution": requested_resolution,
        "status": "Reclamo iniciado",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_csv(COMPLAINTS_FILE, df)
    return row


def list_complaints(booking_id: str | None = None) -> pd.DataFrame:
    df = load_complaints()
    if booking_id:
        df = df[df["booking_id"] == booking_id]
    return df.sort_values("created_at", ascending=False).reset_index(drop=True) if not df.empty else df
