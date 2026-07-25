"""Calificaciones post-servicio."""

from datetime import datetime

import pandas as pd

from services.data_store import RATINGS_FILE, read_csv, write_csv
from services.home_history import add_to_history
from services.reviews import add_review

RATING_COLUMNS = [
    "booking_id", "rating", "comment", "completion_photo_note",
    "warranty_requested", "warranty_status", "warranty_notes", "submitted_at",
]


def load_ratings() -> pd.DataFrame:
    return read_csv(RATINGS_FILE, RATING_COLUMNS)


def get_rating(booking_id: str) -> dict | None:
    df = load_ratings()
    match = df[df["booking_id"] == booking_id]
    if match.empty:
        return None
    row = match.iloc[0].to_dict()
    row["warranty_requested"] = str(row.get("warranty_requested", "")).lower() in ("true", "1", "yes")
    try:
        row["rating"] = int(float(row["rating"])) if row.get("rating") else None
    except (TypeError, ValueError):
        row["rating"] = None
    return row


def submit_completion(
    booking: dict, rating: int, comment: str, work_completed: str,
    photo_note: str = "",
) -> dict:
    if get_rating(booking["id"]):
        return get_rating(booking["id"]) or {}
    df = load_ratings()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = {
        "booking_id": booking["id"],
        "rating": str(rating),
        "comment": comment,
        "completion_photo_note": photo_note,
        "warranty_requested": "False",
        "warranty_status": "No solicitada",
        "warranty_notes": "",
        "submitted_at": now,
    }
    existing = df[df["booking_id"] == booking["id"]]
    if existing.empty:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        for k, v in row.items():
            df.loc[df["booking_id"] == booking["id"], k] = v
    write_csv(RATINGS_FILE, df)

    add_review(
        booking["professional_id"], booking["customer_name"], rating, comment,
        booking.get("locality") or booking.get("neighborhood", ""),
        booking["service_type"], booking_id=booking["id"],
    )
    final_price = float(booking.get("approved_price") or booking.get("initial_price") or 0)
    add_to_history(
        booking_id=booking["id"],
        neighborhood=booking["neighborhood"],
        service_category=booking["service_type"],
        reported_problem=booking["problem_description"],
        work_completed=work_completed,
        professional_name=booking["professional_name"],
        final_price=final_price,
        rating=rating,
        guarantee_status=booking.get("guarantee_status", "Cobertura activa"),
        notes=comment,
    )
    return row


def request_warranty(booking_id: str, notes: str) -> dict:
    df = load_ratings()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = df[df["booking_id"] == booking_id]
    if existing.empty:
        row = {
            "booking_id": booking_id, "rating": "", "comment": "",
            "completion_photo_note": "", "warranty_requested": "True",
            "warranty_status": "En revisión", "warranty_notes": notes, "submitted_at": now,
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df.loc[df["booking_id"] == booking_id, "warranty_requested"] = "True"
        df.loc[df["booking_id"] == booking_id, "warranty_status"] = "En revisión"
        df.loc[df["booking_id"] == booking_id, "warranty_notes"] = notes
    write_csv(RATINGS_FILE, df)
    return df[df["booking_id"] == booking_id].iloc[0].to_dict()
