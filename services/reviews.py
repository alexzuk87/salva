"""Reseñas verificadas de clientes."""

from datetime import datetime

import pandas as pd

from services.data_store import PROFESSIONALS_FILE, REVIEWS_FILE, read_csv, write_csv

REVIEW_COLUMNS = [
    "id", "booking_id", "professional_id", "customer_name", "rating", "comment",
    "neighborhood", "service_type", "created_at", "verified",
]

SEED = [
    ("REV001", "PRO001", "Lucía Fernández", 5, "Solucionó la pérdida al toque. Muy prolija.", "Palermo", "Plomería", "2026-04-12", True),
    ("REV002", "PRO001", "Martín Acosta", 5, "Precio justo y trabajo garantizado.", "Recoleta", "Climatización", "2026-03-28", True),
    ("REV003", "PRO002", "Jorge Pérez", 5, "Instaló tomas nuevas sin desorden.", "Villa Crespo", "Electricidad", "2026-05-01", True),
    ("REV004", "PRO002", "Silvia Ramos", 5, "Reparó la heladera el mismo día.", "Palermo", "Reparación de electrodomésticos", "2026-04-20", True),
    ("REV005", "PRO003", "Paula Méndez", 5, "Dejó el departamento impecable.", "Recoleta", "Limpieza", "2026-05-10", True),
    ("REV006", "PRO006", "Diego Castro", 5, "Emergencia resuelta en menos de 1 hora.", "Palermo", "Climatización", "2026-05-18", True),
    ("REV007", "PRO006", "Valentina Ruiz", 5, "Precio transparente y puntual.", "Recoleta", "Electricidad", "2026-04-25", True),
    ("REV008", "PRO004", "Gabriela Soto", 5, "Transformó el jardín. Súper recomendable.", "Belgrano", "Jardinería", "2026-04-08", True),
]


def seed_reviews() -> None:
    if not REVIEWS_FILE.exists():
        rows = [
            {"id": r[0], "booking_id": "", "professional_id": r[1], "customer_name": r[2], "rating": r[3],
             "comment": r[4], "neighborhood": r[5], "service_type": r[6], "created_at": r[7],
             "verified": r[8]}
            for r in SEED
        ]
        write_csv(REVIEWS_FILE, pd.DataFrame(rows))
        return
    df = read_csv(REVIEWS_FILE, REVIEW_COLUMNS)
    write_csv(REVIEWS_FILE, df)


def load_reviews() -> pd.DataFrame:
    seed_reviews()
    df = read_csv(REVIEWS_FILE, REVIEW_COLUMNS)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    return df


def get_reviews_for_professional(professional_id: str, limit: int = 3) -> pd.DataFrame:
    df = load_reviews()
    pro = df[df["professional_id"] == professional_id]
    return pro.sort_values("created_at", ascending=False).head(limit) if not pro.empty else pro


def count_verified_reviews(professional_id: str) -> int:
    df = load_reviews()
    pro = df[df["professional_id"] == professional_id]
    verified = pro["verified"].map(lambda v: str(v).lower() in ("true", "1", "yes"))
    return int(verified.sum()) if not pro.empty else 0


def next_id_reviews(df: pd.DataFrame) -> str:
    if df.empty:
        return "REV001"
    nums = df["id"].str.replace("REV", "", regex=False).astype(int)
    return f"REV{nums.max() + 1:03d}"


def update_professional_rating(professional_id: str) -> None:
    from services.professionals import PROFESSIONAL_COLUMNS

    df = load_reviews()
    pro_reviews = df[df["professional_id"] == professional_id]
    if pro_reviews.empty:
        return
    avg = pro_reviews["rating"].mean()
    pros = read_csv(PROFESSIONALS_FILE, PROFESSIONAL_COLUMNS)
    idx = pros[pros["id"] == professional_id].index
    if not idx.empty:
        pros.loc[idx, "rating"] = str(round(avg, 1))
        write_csv(PROFESSIONALS_FILE, pros)


def add_review(
    professional_id: str, customer_name: str, rating: int, comment: str,
    neighborhood: str, service_type: str, booking_id: str = "",
) -> None:
    df = load_reviews()
    if booking_id and not df[df["booking_id"] == booking_id].empty:
        return
    row = {
        "id": next_id_reviews(df),
        "booking_id": booking_id,
        "professional_id": professional_id,
        "customer_name": customer_name,
        "rating": str(rating),
        "comment": comment,
        "neighborhood": neighborhood,
        "service_type": service_type,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "verified": "True",
    }
    write_csv(REVIEWS_FILE, pd.concat([df, pd.DataFrame([row])], ignore_index=True))
    update_professional_rating(professional_id)
