"""Barrios y estadísticas locales."""

import pandas as pd

from services.data_store import NEIGHBORHOOD_JOBS_FILE, read_csv, write_csv

NEIGHBORHOODS = [
    "Palermo", "Recoleta", "Belgrano", "Caballito", "Almagro",
    "Villa Crespo", "Nuñez", "San Telmo", "Puerto Madero", "Colegiales",
]

NEIGHBORHOOD_JOB_COLUMNS = ["professional_id", "neighborhood", "jobs_completed"]

SEED = [
    ("PRO001", "Palermo", 48), ("PRO001", "Recoleta", 31), ("PRO001", "Belgrano", 22),
    ("PRO002", "Palermo", 35), ("PRO002", "Villa Crespo", 41), ("PRO002", "Almagro", 28),
    ("PRO003", "Recoleta", 52), ("PRO003", "Puerto Madero", 38), ("PRO003", "San Telmo", 19),
    ("PRO004", "Belgrano", 44), ("PRO004", "Nuñez", 36), ("PRO004", "Colegiales", 29),
    ("PRO005", "Caballito", 27), ("PRO005", "Almagro", 33),
    ("PRO006", "Palermo", 61), ("PRO006", "Recoleta", 47), ("PRO006", "Belgrano", 39),
    ("PRO007", "Villa Crespo", 40), ("PRO007", "Palermo", 32),
    ("PRO008", "Caballito", 22), ("PRO008", "Almagro", 18),
]


def seed_neighborhood_jobs() -> None:
    if NEIGHBORHOOD_JOBS_FILE.exists():
        return
    rows = [{"professional_id": r[0], "neighborhood": r[1], "jobs_completed": r[2]} for r in SEED]
    write_csv(NEIGHBORHOOD_JOBS_FILE, pd.DataFrame(rows))


def load_neighborhood_jobs() -> pd.DataFrame:
    seed_neighborhood_jobs()
    df = read_csv(NEIGHBORHOOD_JOBS_FILE, NEIGHBORHOOD_JOB_COLUMNS)
    df["jobs_completed"] = pd.to_numeric(df["jobs_completed"], errors="coerce").fillna(0).astype(int)
    return df


def jobs_in_neighborhood(professional_id: str, neighborhood: str) -> int:
    df = load_neighborhood_jobs()
    match = df[(df["professional_id"] == professional_id) & (df["neighborhood"] == neighborhood)]
    return int(match.iloc[0]["jobs_completed"]) if not match.empty else 0
