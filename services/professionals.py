"""Descubrimiento y recomendación de profesionales."""

from pathlib import Path

import pandas as pd

from services.data_store import PROFESSIONALS_FILE, read_csv, write_csv
from services.scheduling import URGENCY_LEVELS
from services.reviews import count_verified_reviews

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "professionals"

PROFESSIONAL_COLUMNS = [
    "id", "name", "specialty", "service_types", "rating", "completed_jobs",
    "verified", "identity_verified", "matricula_verified", "experience_years",
    "base_price", "price_type", "availability", "bank_alias", "photo_url",
    "whatsapp", "eta_base_minutes", "province", "city", "coverage_cities", "neighborhoods",
]

SERVICE_TYPES = [
    "Plomería",
    "Electricidad",
    "Climatización",
    "Gasista",
    "Limpieza",
    "Pintura",
    "Jardinería",
    "Reparación de electrodomésticos",
    "Mantenimiento general",
]

URGENCY_MULTIPLIERS = {
    "Emergencia": 1.35,
    "Hoy": 1.15,
    "Lo antes posible": 1.15,
    "Programado": 1.0,
}

# id, name, specialty, services, rating, jobs, ver, idv, mat, exp, price, ptype, avail, alias, avatar, eta, prov, city, coverage, hoods
SEED = [
    ("PRO001", "María González", "Plomera matriculada", "Plomería,Climatización", 4.9, 312, True, True, True, 12, 85000, "Precio orientativo", "08:00-20:00", "salva.maria.gonzalez", "pro001", 35, "Ciudad Autónoma de Buenos Aires", "Ciudad Autónoma de Buenos Aires", "CABA,GABA", "Palermo,Recoleta,Belgrano"),
    ("PRO002", "Carlos Ruiz", "Electricista", "Electricidad,Reparación de electrodomésticos", 4.8, 245, True, True, False, 9, 95000, "Precio cerrado", "09:00-19:00", "salva.carlos.ruiz", "pro002", 40, "Ciudad Autónoma de Buenos Aires", "Ciudad Autónoma de Buenos Aires", "CABA", "Palermo,Villa Crespo,Almagro"),
    ("PRO003", "Ana Torres", "Especialista en limpieza", "Limpieza,Pintura", 4.7, 189, True, True, False, 7, 65000, "Precio cerrado", "08:00-18:00", "salva.ana.torres", "pro003", 30, "Ciudad Autónoma de Buenos Aires", "Ciudad Autónoma de Buenos Aires", "CABA", "Recoleta,San Telmo"),
    ("PRO004", "Roberto Silva", "Técnico HVAC matriculado", "Climatización,Electricidad", 4.9, 278, True, True, True, 15, 110000, "Precio orientativo", "08:00-20:00", "salva.roberto.silva", "pro006", 25, "Ciudad Autónoma de Buenos Aires", "Ciudad Autónoma de Buenos Aires", "CABA", "Belgrano,Nuñez"),
    ("PRO005", "Elena Vargas", "Plomera general", "Plomería,Mantenimiento general", 4.5, 98, True, True, False, 5, 70000, "Precio orientativo", "10:00-20:00", "salva.elena.vargas", "pro005", 50, "Buenos Aires", "La Plata", "Buenos Aires", "Centro,Gonnet"),
    ("PRO006", "Diego Herrera", "Pintor profesional", "Pintura,Mantenimiento general", 4.4, 87, True, True, False, 4, 55000, "Precio orientativo", "08:00-17:00", "salva.diego.herrera", "pro008", 55, "Buenos Aires", "Mar del Plata", "Buenos Aires", "Centro,Guemes"),
    ("PRO007", "Patricia Lima", "Limpieza y jardinería", "Limpieza,Jardinería", 4.6, 134, True, True, False, 6, 60000, "Precio cerrado", "08:00-18:00", "salva.patricia.lima", "pro007", 38, "Córdoba", "Córdoba", "Córdoba", "Centro,Nueva Córdoba"),
    ("PRO008", "Martín Acosta", "Electricista matriculado", "Electricidad,Climatización", 4.8, 201, True, True, True, 11, 92000, "Precio cerrado", "08:00-20:00", "salva.martin.acosta", "pro010", 42, "Córdoba", "Córdoba", "Córdoba,Villa Carlos Paz", "Centro,Alta Gracia"),
    ("PRO009", "Lucía Fernández", "Plomera", "Plomería", 4.7, 156, True, True, False, 8, 78000, "Precio orientativo", "08:00-19:00", "salva.lucia.fernandez", "pro009", 45, "Santa Fe", "Rosario", "Santa Fe", "Centro,Pichincha"),
    ("PRO010", "Jorge Pérez", "Técnico en electrodomésticos", "Reparación de electrodomésticos,Electricidad", 4.6, 143, True, True, False, 10, 88000, "Precio orientativo", "09:00-18:00", "salva.jorge.perez", "pro014", 48, "Santa Fe", "Rosario", "Santa Fe", "Centro,Fisherton"),
    ("PRO011", "Valentina Ruiz", "Gasista matriculada", "Climatización,Mantenimiento general", 4.9, 267, True, True, True, 14, 105000, "Precio orientativo", "08:00-20:00", "salva.valentina.ruiz", "pro013", 32, "Mendoza", "Mendoza", "Mendoza", "Centro,Godoy Cruz"),
    ("PRO012", "Gabriel Soto", "Jardinero", "Jardinería,Mantenimiento general", 4.5, 112, True, True, False, 7, 72000, "Precio orientativo", "07:00-17:00", "salva.gabriel.soto", "pro012", 50, "Mendoza", "Mendoza", "Mendoza", "Centro,Luján"),
    ("PRO013", "Camila Ríos", "Cerrajera", "Mantenimiento general", 4.7, 178, True, True, False, 9, 82000, "Precio cerrado", "00:00-23:59", "salva.camila.rios", "pro011", 28, "Tucumán", "San Miguel de Tucumán", "Tucumán", "Centro,Yerba Buena"),
    ("PRO014", "Fernando Díaz", "Electricista", "Electricidad", 4.6, 165, True, True, True, 13, 98000, "Precio cerrado", "08:00-20:00", "salva.fernando.diaz", "pro002", 38, "Salta", "Salta", "Salta", "Centro,Grand Bourg"),
    ("PRO015", "Sofía Navarro", "Plomera", "Plomería,Climatización", 4.8, 198, True, True, True, 10, 90000, "Precio orientativo", "08:00-19:00", "salva.sofia.navarro", "pro001", 36, "Neuquén", "Neuquén", "Neuquén", "Centro,Cipolletti"),
    ("PRO016", "Ricardo Moya", "Pintor y albañil", "Pintura,Mantenimiento general", 4.4, 95, True, True, False, 6, 58000, "Precio orientativo", "08:00-18:00", "salva.ricardo.moya", "pro004", 52, "Chubut", "Comodoro Rivadavia", "Chubut", "Centro,Km 3"),
]

BADGE_TOOLTIP = "Información simulada para este prototipo académico."


def avatar_path(pro_id: str) -> str:
    jpg = ASSETS / f"{pro_id.lower()}.jpg"
    if jpg.is_file():
        return f"assets/professionals/{pro_id.lower()}.jpg"
    svg = Path(__file__).resolve().parent.parent / "assets" / "avatars" / f"{pro_id.lower()}.svg"
    if svg.is_file():
        return f"assets/avatars/{pro_id.lower()}.svg"
    return ""


def seed_professionals() -> None:
    if not PROFESSIONALS_FILE.exists():
        _write_seed()
        return
    raw = pd.read_csv(PROFESSIONALS_FILE, dtype=str, keep_default_na=False)
    seed_map = {r[0]: r for r in SEED}
    for col in PROFESSIONAL_COLUMNS:
        if col not in raw.columns:
            raw[col] = ""
    for idx, row in raw.iterrows():
        pid = row.get("id", "")
        if pid not in seed_map:
            continue
        r = seed_map[pid]
        raw.at[idx, "name"] = r[1]
        raw.at[idx, "specialty"] = r[2]
        raw.at[idx, "service_types"] = r[3]
        raw.at[idx, "availability"] = r[12]
        if "pravatar" in str(row.get("photo_url", "")) or not str(row.get("photo_url", "")).startswith("assets/professionals"):
            raw.at[idx, "photo_url"] = f"assets/professionals/{pid.lower()}.jpg"
        if not str(row.get("province", "")).strip():
            raw.at[idx, "province"] = r[16]
            raw.at[idx, "city"] = r[17]
            raw.at[idx, "coverage_cities"] = r[18]
        raw.at[idx, "whatsapp"] = ""
    write_csv(PROFESSIONALS_FILE, raw[PROFESSIONAL_COLUMNS])
    existing_ids = set(raw["id"].tolist())
    new_rows = []
    for r in SEED:
        if r[0] in existing_ids:
            continue
        avatar = r[14]
        new_rows.append({
            "id": r[0], "name": r[1], "specialty": r[2], "service_types": r[3],
            "rating": r[4], "completed_jobs": r[5], "verified": r[6],
            "identity_verified": r[7], "matricula_verified": r[8],
            "experience_years": r[9], "base_price": r[10], "price_type": r[11],
            "availability": r[12], "bank_alias": r[13], "photo_url": f"assets/professionals/{r[0].lower()}.jpg",
            "whatsapp": "", "eta_base_minutes": r[15], "province": r[16],
            "city": r[17], "coverage_cities": r[18], "neighborhoods": r[19],
        })
    if new_rows:
        write_csv(PROFESSIONALS_FILE, pd.concat([raw[PROFESSIONAL_COLUMNS], pd.DataFrame(new_rows)], ignore_index=True))


def _write_seed() -> None:
    rows = []
    for r in SEED:
        avatar = r[14]
        rows.append({
            "id": r[0], "name": r[1], "specialty": r[2], "service_types": r[3],
            "rating": r[4], "completed_jobs": r[5], "verified": r[6],
            "identity_verified": r[7], "matricula_verified": r[8],
            "experience_years": r[9], "base_price": r[10], "price_type": r[11],
            "availability": r[12], "bank_alias": r[13], "photo_url": f"assets/professionals/{r[0].lower()}.jpg",
            "whatsapp": "", "eta_base_minutes": r[15], "province": r[16],
            "city": r[17], "coverage_cities": r[18], "neighborhoods": r[19],
        })
    write_csv(PROFESSIONALS_FILE, pd.DataFrame(rows))


def load_professionals() -> pd.DataFrame:
    seed_professionals()
    df = read_csv(PROFESSIONALS_FILE, PROFESSIONAL_COLUMNS)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["completed_jobs"] = pd.to_numeric(df["completed_jobs"], errors="coerce").astype("Int64")
    df["base_price"] = pd.to_numeric(df["base_price"], errors="coerce")
    df["experience_years"] = pd.to_numeric(df["experience_years"], errors="coerce").fillna(0).astype(int)
    df["eta_base_minutes"] = pd.to_numeric(df["eta_base_minutes"], errors="coerce").fillna(45).astype(int)
    for col in ("verified", "identity_verified", "matricula_verified"):
        df[col] = df[col].map(lambda v: str(v).lower() in ("true", "1", "yes"))
    return df


def estimate_price(base_price: float, urgency: str) -> float:
    return round(float(base_price) * URGENCY_MULTIPLIERS.get(urgency, 1.0), 0)


def estimate_arrival(urgency: str, eta_base: int, slot_match: bool) -> str:
    base = int(eta_base)
    if urgency in ("Emergencia", "Hoy"):
        low = max(20, base - 15)
        return f"{low}–{low + 30} min"
    if urgency == "Lo antes posible":
        return f"{base}–{base + 50} min"
    return f"{base + 15}–{base + 45} min" if slot_match else "En horario acordado"


def recommend_professionals(
    service_type: str,
    urgency: str,
    appointment_time: str,
    neighborhood: str = "",
    province: str = "",
    locality: str = "",
    verified_only: bool = True,
) -> pd.DataFrame:
    from services.service_categories import category_match_terms, category_specialty_keywords

    df = load_professionals()
    match_terms = set(category_match_terms(service_type) or [service_type])
    specialty_kw = category_specialty_keywords(service_type)

    def _matches(row) -> bool:
        types = [x.strip() for x in str(row.get("service_types", "")).split(",") if x.strip()]
        if any(term in types for term in match_terms):
            return True
        specialty = str(row.get("specialty", "")).casefold()
        return any(kw in specialty for kw in specialty_kw)

    mask = df.apply(_matches, axis=1)
    candidates = df[mask].copy()
    if verified_only:
        candidates = candidates[candidates["verified"]]
    if province:
        prov_match = candidates["province"].eq(province) | candidates["coverage_cities"].apply(
            lambda c: province in [x.strip() for x in str(c).split(",")]
        )
        if prov_match.any():
            candidates = candidates[prov_match]
    if locality:
        loc_match = candidates["city"].str.lower().eq(locality.lower()) | candidates["coverage_cities"].apply(
            lambda c: locality.lower() in str(c).lower()
        )
        if loc_match.any():
            candidates = candidates[loc_match]
    if candidates.empty:
        candidates = df[mask].copy()
        if verified_only:
            candidates = candidates[candidates["verified"]]

    candidates["estimated_price"] = candidates["base_price"].apply(lambda p: estimate_price(p, urgency))
    candidates["slot_match"] = True
    candidates["verified_reviews"] = candidates["id"].apply(count_verified_reviews)
    candidates["neighborhood_jobs"] = candidates["completed_jobs"].apply(lambda j: max(int(j or 0) // 6, 12))
    candidates["eta_label"] = candidates.apply(
        lambda r: estimate_arrival(urgency, r["eta_base_minutes"], r["slot_match"]), axis=1
    )
    candidates["eta_minutes"] = candidates["eta_base_minutes"]
    return candidates


def sort_professionals(df: pd.DataFrame, sort_by: str) -> pd.DataFrame:
    if df.empty:
        return df
    if sort_by == "Menor precio":
        return df.sort_values("estimated_price").reset_index(drop=True)
    if sort_by == "Llega antes":
        return df.sort_values("eta_minutes").reset_index(drop=True)
    if sort_by == "Más trabajos en tu zona":
        return df.sort_values("neighborhood_jobs", ascending=False).reset_index(drop=True)
    if sort_by == "Disponibilidad":
        return df.sort_values("slot_match", ascending=False).reset_index(drop=True)
    if sort_by == "Disponible hoy":
        return df.sort_values("eta_minutes").reset_index(drop=True)
    return df.sort_values("rating", ascending=False).reset_index(drop=True)


def get_professional(professional_id: str) -> dict | None:
    df = load_professionals()
    match = df[df["id"] == professional_id]
    return match.iloc[0].to_dict() if not match.empty else None
