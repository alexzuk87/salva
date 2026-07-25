"""Personajes animados por categoría de servicio."""

import base64
import html
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAR_DIR = PROJECT_ROOT / "assets" / "service-characters"

HOME_CATEGORIES = [
    ("Plomería", "plomeria", "Plomería", "Pérdidas, cañerías y grifería"),
    ("Electricidad", "electricidad", "Electricidad", "Instalaciones y urgencias"),
    ("Gas", "gas", "Climatización", "Revisión y reparación"),
    ("Cerrajería", "cerrajeria", "Mantenimiento general", "Accesos y cerraduras"),
    ("Limpieza", "limpieza", "Limpieza", "Limpieza profunda y mantenimiento"),
    ("Pintura", "pintura", "Pintura", "Interiores y exteriores"),
    ("Electrodomésticos", "electrodomesticos", "Reparación de electrodomésticos", "Reparación y mantenimiento"),
    ("Jardinería", "jardineria", "Jardinería", "Plantas, césped y exteriores"),
    ("Albañilería", "albanileria", "Mantenimiento general", "Reparaciones y obra menor"),
    ("Aire acondicionado", "aire", "Climatización", "Instalación y service"),
    ("Carpintería", "carpinteria", "Mantenimiento general", "Muebles, puertas y medidas"),
    ("Ver todos", "todos", "", "Explorá todas las categorías"),
]

SERVICE_ICON_KEY = {
    "Plomería": "plomeria",
    "Electricidad": "electricidad",
    "Climatización": "aire",
    "Gas": "gas",
    "Limpieza": "limpieza",
    "Pintura": "pintura",
    "Jardinería": "jardineria",
    "Reparación de electrodomésticos": "electrodomesticos",
    "Mantenimiento general": "albanileria",
    "Albañilería": "albanileria",
    "Aire acondicionado": "aire",
    "Carpintería": "carpinteria",
}

CATEGORY_ACCENTS = {
    "plomeria": "#38BDF8",
    "electricidad": "#FACC15",
    "gas": "#FB923C",
    "cerrajeria": "#F59E0B",
    "limpieza": "#2DD4BF",
    "pintura": "#A78BFA",
    "electrodomesticos": "#22D3EE",
    "jardineria": "#84CC16",
    "albanileria": "#EA580C",
    "aire": "#7DD3FC",
    "carpinteria": "#A16207",
    "todos": "#365CF5",
}


def character_image_path(key: str) -> Path | None:
    path = CHAR_DIR / f"{key}.svg"
    if path.is_file():
        return path
    fallback = CHAR_DIR / "todos.svg"
    return fallback if fallback.is_file() else None


def character_img_html(key: str, size: int = 48, css_class: str = "svc-character") -> str:
    path = CHAR_DIR / f"{key}.svg"
    if not path.is_file():
        path = CHAR_DIR / "todos.svg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<img class="{css_class}" src="data:image/svg+xml;base64,{b64}" '
        f'width="{size}" height="{size}" alt="{html.escape(key)}"/>'
    )


def category_card_html(label: str, key: str, descriptor: str, selected: bool = False) -> str:
    accent = CATEGORY_ACCENTS.get(key, "#365CF5")
    sel = " cat-card-selected" if selected else ""
    char = character_img_html(key, 48, f"svc-character svc-{key}")
    return (
        f'<div class="cat-service-card{sel}" style="--cat-accent:{accent}">'
        f'<div class="cat-char-wrap">{char}</div>'
        f'<div class="cat-label">{html.escape(label)}</div>'
        f'<div class="cat-desc">{html.escape(descriptor)}</div></div>'
    )
