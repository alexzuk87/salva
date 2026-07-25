"""Iconos lineales animados para SALVA."""

from services.service_characters import HOME_CATEGORIES, SERVICE_ICON_KEY  # noqa: F401

ICON_STROKE = "#365CF5"
ICON_SIZE = 24


def _svg(path_d: str, size: int = ICON_SIZE, stroke: str = ICON_STROKE, extra: str = "", anim_class: str = "") -> str:
    cls = f' class="salva-icon {anim_class}"' if anim_class else ' class="salva-icon"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round"{cls}>{extra}{path_d}</svg>'
    )


ICONS = {
    "plomeria": _svg(
        '<path d="M4 14h16M6 14V8a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v6M9 18v2M15 18v2"/>'
        '<circle class="anim-drop" cx="12" cy="10" r="1.5" fill="#365CF5" stroke="none"/>',
        anim_class="icon-plomeria",
    ),
    "electricidad": _svg('<path class="anim-bolt" d="M13 2L4 14h7l-1 8 10-14h-7l0-6"/>', anim_class="icon-electricidad"),
    "gas": _svg(
        '<circle cx="12" cy="14" r="2"/><path class="anim-flame" d="M12 4c0 4-3 5-3 8a3 3 0 0 0 6 0c0-3-3-4-3-8z"/>',
        anim_class="icon-gas",
    ),
    "cerrajeria": _svg(
        '<path d="M7 11V8a5 5 0 0 1 10 0v3"/><rect x="5" y="11" width="14" height="10" rx="2"/>'
        '<path class="anim-shackle" d="M12 15v2"/>',
        anim_class="icon-cerrajeria",
    ),
    "limpieza": _svg(
        '<path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"/>'
        '<path class="anim-sparkle" d="M5 19h14"/>',
        anim_class="icon-limpieza",
    ),
    "pintura": _svg(
        '<path d="M14 4h4v4l-7 7a2 2 0 1 1-2.8-2.8L14 4z"/><path class="anim-brush" d="M6 20h12"/>',
        anim_class="icon-pintura",
    ),
    "electro": _svg(
        '<rect x="4" y="4" width="16" height="16" rx="2"/><circle class="anim-led" cx="12" cy="12" r="2" fill="#365CF5" stroke="none"/>',
        anim_class="icon-electro",
    ),
    "jardineria": _svg(
        '<path class="anim-leaf" d="M12 20V10"/><path d="M12 10C12 10 8 8 6 12c2 2 6 2 6-2z"/>'
        '<path d="M12 10c0 0 4-2 6 2-2 2-6 2-6-2z"/>',
        anim_class="icon-jardineria",
    ),
    "todos": _svg('<path d="M4 6h16M4 12h16M4 18h10"/>', anim_class="icon-todos"),
    "verified": _svg('<path d="M12 3l2.2 4.5 5 .7-3.6 3.5.9 5-4.5-2.4-4.5 2.4.9-5L4.8 8.2l5-.7L12 3z"/>', stroke="#18A875"),
    "precio": _svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9 10h4a2 2 0 1 1 0 4H9"/>'),
    "tracking": _svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    "garantia": _svg('<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"/>'),
    "empty": _svg('<path d="M4 14h16M6 14V8a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v6"/>', stroke="#365CF5"),
    "libreta": _svg('<path d="M6 4h11a2 2 0 0 1 2 2v14H8a2 2 0 0 1-2-2V4z"/><path d="M8 4v16"/>'),
    "reservas": _svg('<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>'),
    "chat": _svg('<path d="M4 6h16v10H8l-4 4V6z"/>'),
}

HOME_CATEGORIES_LEGACY = HOME_CATEGORIES  # compat

BENEFITS = [
    ("verified", "Profesionales verificados", "Identidad y experiencia simuladas para el prototipo."),
    ("precio", "Precio claro", "Sabés el monto antes de confirmar."),
    ("tracking", "Seguimiento en tiempo real", "Estado del servicio paso a paso."),
    ("garantia", "Garantía SALVA", "Respaldo post-servicio y canal de reclamos."),
]
