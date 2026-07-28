"""Mapeo central de categorías visibles ↔ valores internos de SALVA."""

from __future__ import annotations

from typing import Any

# Clave estable → metadatos de categoría.
# - label: texto amigable en la UI
# - internal: valor guardado en reservas / diagnosis / CSV (compatible con dominio)
# - match_aliases: valores adicionales para buscar profesionales sin alterar CSV
# - icon: clave de personaje/ícono
# - descriptor: ayuda corta del botón
CATEGORY_CATALOG: dict[str, dict[str, Any]] = {
    "plomeria": {
        "label": "Plomería",
        "internal": "Plomería",
        "match_aliases": ["Plomería"],
        "icon": "plomeria",
        "descriptor": "Pérdidas, cañerías y grifería",
    },
    "electricidad": {
        "label": "Electricidad",
        "internal": "Electricidad",
        "match_aliases": ["Electricidad"],
        "icon": "electricidad",
        "descriptor": "Instalaciones y urgencias",
    },
    "gas": {
        "label": "Gas",
        "internal": "Gasista",
        "match_aliases": ["Gasista", "Climatización"],
        "specialty_keywords": ["gasista"],
        "icon": "gas",
        "descriptor": "Revisión y reparación",
    },
    "cerrajeria": {
        "label": "Cerrajería",
        "internal": "Mantenimiento general",
        "match_aliases": ["Mantenimiento general"],
        "specialty_keywords": ["cerraj"],
        "icon": "cerrajeria",
        "descriptor": "Accesos y cerraduras",
    },
    "limpieza": {
        "label": "Limpieza",
        "internal": "Limpieza",
        "match_aliases": ["Limpieza"],
        "icon": "limpieza",
        "descriptor": "Limpieza profunda y mantenimiento",
    },
    "pintura": {
        "label": "Pintura",
        "internal": "Pintura",
        "match_aliases": ["Pintura"],
        "icon": "pintura",
        "descriptor": "Interiores y exteriores",
    },
    "electrodomesticos": {
        "label": "Electrodomésticos",
        "internal": "Reparación de electrodomésticos",
        "match_aliases": ["Reparación de electrodomésticos"],
        "icon": "electrodomesticos",
        "descriptor": "Reparación y mantenimiento",
    },
    "jardineria": {
        "label": "Jardinería",
        "internal": "Jardinería",
        "match_aliases": ["Jardinería"],
        "icon": "jardineria",
        "descriptor": "Plantas, césped y exteriores",
    },
    "albanileria": {
        "label": "Albañilería",
        "internal": "Mantenimiento general",
        "match_aliases": ["Mantenimiento general"],
        "specialty_keywords": ["albañ", "alban"],
        "icon": "albanileria",
        "descriptor": "Reparaciones y obra menor",
    },
    "aire": {
        "label": "Aire acondicionado",
        "internal": "Climatización",
        "match_aliases": ["Climatización"],
        "specialty_keywords": ["hvac", "aire", "climat"],
        "icon": "aire",
        "descriptor": "Instalación y service",
    },
    "carpinteria": {
        "label": "Carpintería",
        "internal": "Mantenimiento general",
        "match_aliases": ["Mantenimiento general"],
        "specialty_keywords": ["carpint"],
        "icon": "carpinteria",
        "descriptor": "Muebles, puertas y medidas",
    },
}

# Orden de la grilla de inicio / formulario
CATEGORY_ORDER = [
    "plomeria",
    "electricidad",
    "gas",
    "cerrajeria",
    "limpieza",
    "pintura",
    "electrodomesticos",
    "jardineria",
    "albanileria",
    "aire",
    "carpinteria",
]

_LABEL_TO_KEY = {meta["label"].casefold(): key for key, meta in CATEGORY_CATALOG.items()}
_INTERNAL_TO_KEYS: dict[str, list[str]] = {}
for _key, _meta in CATEGORY_CATALOG.items():
    _INTERNAL_TO_KEYS.setdefault(str(_meta["internal"]), []).append(_key)


def category_key(value: str | None) -> str:
    """Resuelve una clave estable desde label, key o valor interno."""
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw in CATEGORY_CATALOG:
        return raw
    by_label = _LABEL_TO_KEY.get(raw.casefold())
    if by_label:
        return by_label
    # Si llega un valor interno ambiguo (p. ej. Climatización), preferir aire.
    keys = _INTERNAL_TO_KEYS.get(raw, [])
    if "aire" in keys:
        return "aire"
    if "gas" in keys:
        return "gas"
    return keys[0] if keys else ""


def category_label(value: str | None) -> str:
    key = category_key(value)
    if key:
        return str(CATEGORY_CATALOG[key]["label"])
    return (value or "").strip()


def category_internal(value: str | None) -> str:
    """Valor interno para reservas, diagnosis y búsquedas."""
    key = category_key(value)
    if key:
        return str(CATEGORY_CATALOG[key]["internal"])
    return (value or "").strip()


def category_match_terms(value: str | None) -> list[str]:
    """Términos usados para matchear profesionales (sin alterar CSV)."""
    key = category_key(value)
    if not key:
        raw = (value or "").strip()
        return [raw] if raw else []
    aliases = CATEGORY_CATALOG[key].get("match_aliases") or [CATEGORY_CATALOG[key]["internal"]]
    return [str(a) for a in aliases]


def category_specialty_keywords(value: str | None) -> list[str]:
    key = category_key(value)
    if not key:
        return []
    return [str(k).casefold() for k in (CATEGORY_CATALOG[key].get("specialty_keywords") or [])]


def home_categories_tuples() -> list[tuple[str, str, str, str]]:
    """Compatibilidad con el formato histórico de HOME_CATEGORIES."""
    rows = [
        (
            str(CATEGORY_CATALOG[key]["label"]),
            str(CATEGORY_CATALOG[key]["icon"]),
            str(CATEGORY_CATALOG[key]["internal"]),
            str(CATEGORY_CATALOG[key]["descriptor"]),
        )
        for key in CATEGORY_ORDER
    ]
    rows.append(("Ver todos", "todos", "", "Explorá todas las categorías"))
    return rows


def resolve_selection(label: str, mapped: str | None = None) -> dict[str, str]:
    """Normaliza una selección de UI a key/label/internal."""
    key = category_key(label) or category_key(mapped)
    if not key and mapped and mapped != "__all__":
        key = category_key(mapped)
    if not key:
        return {
            "key": "",
            "label": label or "",
            "internal": mapped or label or "",
        }
    meta = CATEGORY_CATALOG[key]
    return {
        "key": key,
        "label": str(meta["label"]),
        "internal": str(meta["internal"]),
    }
