"""SALVA Predict — recomendaciones preventivas."""

from datetime import date, timedelta

import pandas as pd

from services.data_store import HOME_PROFILES_FILE, read_csv, write_csv
from services.home_history import load_history

PROFILE_COLUMNS = [
    "id", "first_name", "last_name", "home_type", "age_years", "rooms",
    "has_gas", "has_ac", "last_electrical_review", "province", "locality",
    "neighborhood", "address", "updated_at",
]

GENERAL_TIPS = [
    ("Revisar calefón antes del invierno", "Evita fallas en temporada de frío", "Alta", 45000, 85000),
    ("Controlar instalación eléctrica", "Seguridad y prevención de cortocircuitos", "Alta", 35000, 70000),
    ("Limpiar filtros del aire acondicionado", "Mejora eficiencia y calidad del aire", "Media", 15000, 35000),
    ("Revisar pérdidas de agua", "Ahorro y prevención de daños", "Media", 25000, 55000),
    ("Pintura preventiva por humedad", "Protege muros y evita moho", "Baja", 80000, 150000),
]


def load_profile() -> dict | None:
    df = read_csv(HOME_PROFILES_FILE, PROFILE_COLUMNS)
    if df.empty:
        return None
    return df.iloc[-1].to_dict()


def save_profile(
    home_type: str,
    age: int,
    rooms: int,
    has_gas: bool,
    has_ac: bool,
    last_electrical: int,
    neighborhood: str,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    province: str | None = None,
    locality: str | None = None,
    address: str | None = None,
) -> dict:
    from datetime import datetime
    current = load_profile() or {}
    row = {
        "id": "HP001",
        "first_name": current.get("first_name", "") if first_name is None else first_name,
        "last_name": current.get("last_name", "") if last_name is None else last_name,
        "home_type": home_type,
        "age_years": str(age),
        "rooms": str(rooms),
        "has_gas": str(has_gas),
        "has_ac": str(has_ac),
        "last_electrical_review": str(last_electrical),
        "province": current.get("province", "") if province is None else province,
        "locality": current.get("locality", "") if locality is None else locality,
        "neighborhood": neighborhood,
        "address": current.get("address", "") if address is None else address,
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
    }
    write_csv(HOME_PROFILES_FILE, pd.DataFrame([row]))
    return row


def generate_recommendations() -> list[dict]:
    history = load_history()
    profile = load_profile()
    recs = []
    today = date.today()

    for title, reason, priority, low, high in GENERAL_TIPS:
        suggested = (today + timedelta(days=30 if priority == "Alta" else 60)).isoformat()
        recs.append({
            "title": title, "reason": reason, "priority": priority,
            "suggested_date": suggested, "cost_low": low, "cost_high": high,
            "source": "Recomendación orientativa generada por SALVA.",
        })

    if profile:
        if str(profile.get("has_gas", "")).lower() in ("true", "1", "yes"):
            recs.insert(0, {
                "title": "Inspección anual de instalación de gas",
                "reason": "Tu vivienda tiene gas — revisión recomendada por seguridad.",
                "priority": "Alta",
                "suggested_date": (today + timedelta(days=14)).isoformat(),
                "cost_low": 40000, "cost_high": 75000,
                "source": "Recomendación orientativa generada por SALVA.",
            })
        if str(profile.get("has_ac", "")).lower() in ("true", "1", "yes"):
            recs.insert(1, {
                "title": "Service de aire acondicionado",
                "reason": "Mantenimiento preventivo según perfil del hogar.",
                "priority": "Media",
                "suggested_date": (today + timedelta(days=21)).isoformat(),
                "cost_low": 20000, "cost_high": 45000,
                "source": "Recomendación orientativa generada por SALVA.",
            })

    if not history.empty:
        last = history.sort_values("date", ascending=False).iloc[0]
        recs.append({
            "title": f"Seguimiento post-{last['service_category']}",
            "reason": f"Último servicio: {last['work_completed'] or last['reported_problem']}",
            "priority": "Media",
            "suggested_date": (today + timedelta(days=90)).isoformat(),
            "cost_low": 30000, "cost_high": 60000,
            "source": "Recomendación orientativa generada por SALVA.",
        })

    return recs[:8]


def recommendation_service_type(recommendation: dict) -> str:
    """Mapea una recomendación Predict a una categoría interna válida."""
    text = f"{recommendation.get('title', '')} {recommendation.get('reason', '')}".lower()
    mappings = (
        (("agua", "pérdida", "cañería", "calefón"), "Plomería"),
        (("eléctric", "cortocircuit"), "Electricidad"),
        (("instalación de gas", "revisión de gas", "artefactos a gas", "olor a gas"), "Gasista"),
        (("aire acondicionado", "filtro", "climatización", "split"), "Climatización"),
        (("pintura", "humedad", "muro"), "Pintura"),
        (("limpieza",), "Limpieza"),
        (("jardín", "jardiner"), "Jardinería"),
        (("electrodoméstico",), "Reparación de electrodomésticos"),
    )
    for keywords, service_type in mappings:
        if any(keyword in text for keyword in keywords):
            return service_type
    return "Mantenimiento general"


def predict_intro() -> str:
    return (
        "Según el historial de tu hogar y los datos que cargaste, "
        "estas son las próximas tareas que convendría anticipar."
    )


def narrative_phrases(profile: dict | None, history_df) -> list[str]:
    phrases = []
    if profile and str(profile.get("has_ac", "")).lower() in ("true", "1", "yes"):
        phrases.append("Se acerca una época de mayor uso del aire acondicionado.")
    if profile and str(profile.get("has_gas", "")).lower() in ("true", "1", "yes"):
        phrases.append("Hace más de un año que no registrás una revisión de gas.")
    if profile:
        try:
            yr = int(profile.get("last_electrical_review") or 2020)
            if yr < date.today().year - 1:
                phrases.append("La última intervención eléctrica fue hace varios meses.")
        except ValueError:
            pass
        try:
            age = int(profile.get("age_years") or 0)
            if age >= 15:
                phrases.append("Por la antigüedad de tu vivienda, te recomendamos revisar estas instalaciones.")
        except ValueError:
            pass
    if not phrases:
        phrases.append("Podés preparar este gasto creando un SALVA Objetivo.")
    return phrases
