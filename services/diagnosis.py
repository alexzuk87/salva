"""Diagnóstico orientativo simulado (prototipo académico)."""

from services.pricing import prices_from_professionals
from services.professionals import estimate_price, recommend_professionals

SERVICE_KEYWORDS = {
    "Plomería": ["pérdida", "canilla", "agua", "caño", "inodoro", "desagüe", "plomer"],
    "Electricidad": ["luz", "toma", "cable", "disyuntor", "electric", "enchufe"],
    "Climatización": ["aire", "frío", "calor", "split", "hvac", "clima"],
    "Gasista": ["gas", "calefón", "estufa", "cocina", "garrafa"],
    "Limpieza": ["limpieza", "sucio", "profunda", "higien"],
    "Pintura": ["pintura", "pared", "mancha", "retoque"],
    "Jardinería": ["jardín", "césped", "planta", "poda"],
    "Reparación de electrodomésticos": ["heladera", "lavarropas", "microondas", "electro"],
    "Mantenimiento general": ["puerta", "ventana", "persiana", "manten"],
}


def infer_service_type(description: str, selected: str) -> str:
    text = description.lower()
    scores = {svc: sum(1 for kw in kws if kw in text) for svc, kws in SERVICE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else selected


def build_diagnosis(request: dict) -> dict:
    service = infer_service_type(request["description"], request["service_type"])
    pros = recommend_professionals(
        service,
        request["urgency"],
        request.get("appointment_time") or request.get("preferred_time", ""),
        neighborhood=request.get("neighborhood", ""),
        province=request.get("province", ""),
        locality=request.get("locality", ""),
    )
    if pros.empty:
        low = high = None
    elif "estimated_price" in pros.columns:
        low, high = prices_from_professionals(pros["estimated_price"].tolist())
    else:
        prices = [
            estimate_price(float(p), request["urgency"])
            for p in pros["base_price"].tolist()
        ]
        low, high = prices_from_professionals(prices)
    return {
        "problem_reported": request["description"],
        "recommended_trade": service,
        "urgency": request["urgency"],
        "price_range_low": low,
        "price_range_high": high,
        "professionals_available": len(pros),
        "neighborhood": request.get("locality") or request.get("neighborhood", ""),
        "province": request.get("province", ""),
    }
