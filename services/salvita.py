"""Compañero de marca Salvita."""

from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

STATES = {
    "neutral": "salvita-neutral.svg",
    "waving": "salvita-waving.svg",
    "searching": "salvita-searching.svg",
    "success": "salvita-success.svg",
    "warning": "salvita-warning.svg",
    "travelling": "salvita-travelling.svg",
}

COPY = {
    "neutral": "¿Qué resolvemos hoy?",
    "searching": "Estoy buscando profesionales disponibles cerca tuyo.",
    "success": "Listo, tu reserva quedó confirmada.",
    "travelling": "Tu profesional está en camino.",
    "warning": "Revisemos este detalle juntos.",
    "libreta": "Acá vamos a guardar la historia de tu hogar.",
}


def _read(name: str) -> str:
    path = ASSETS / name
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


def salvita_html(state: str = "neutral", message: str = "", size: int = 56) -> str:
    svg_file = STATES.get(state, STATES["neutral"])
    svg = _read(svg_file)
    if svg and 'width="' not in svg[:120]:
        svg = svg.replace("<svg ", f'<svg width="{size}" height="{size}" ', 1)
    msg = message or COPY.get(state, COPY["neutral"])
    anim = f"salvita-{state}" if state in STATES else "salvita-neutral"
    return (
        f'<div class="salvita-wrap {anim}">'
        f'<div class="salvita-icon">{svg}</div>'
        f'<p class="salvita-msg">{msg}</p></div>'
    )
