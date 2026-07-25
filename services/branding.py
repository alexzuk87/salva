"""Rutas y utilidades de marca SALVA — única fuente de verdad para logo e iconos."""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "ASSETS_DIR",
    "FAVICON",
    "LOGO_HORIZONTAL",
    "SYMBOL",
    "SYMBOL_PNG",
    "SYMBOL_WHITE",
    "logo_header_html",
    "page_icon",
    "read_svg",
    "symbol_white_html",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

LOGO_HORIZONTAL = ASSETS_DIR / "salva-logo-horizontal.svg"
SYMBOL = ASSETS_DIR / "salva-symbol.svg"
SYMBOL_PNG = ASSETS_DIR / "salva-symbol.png"
SYMBOL_WHITE = ASSETS_DIR / "salva-symbol-white.svg"
FAVICON = ASSETS_DIR / "salva-favicon.svg"

_FALLBACK_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 40" fill="none">'
    '<path d="M20 6L32 16V34H24V25H16V34H8V16L20 6Z" stroke="#365CF5" stroke-width="2.2" '
    'stroke-linejoin="round" stroke-linecap="round"/>'
    '<path d="M28 12L30.8 14.8L35 10.5" stroke="#18A875" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<text x="46" y="28" font-family="Inter, Arial, sans-serif" font-size="22" '
    'font-weight="700" fill="#365CF5" letter-spacing="-0.5">SALVA</text></svg>'
)
_FALLBACK_SYMBOL = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">'
    '<path d="M16 4L26 12V28H20V20H12V28H6V12L16 4Z" stroke="#365CF5" '
    'stroke-width="2" stroke-linejoin="round"/></svg>'
)


def read_svg(path: Path) -> str:
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8")
    except OSError:
        pass
    return ""


def logo_header_html() -> str:
    """Logo horizontal SALVA — marca en azul eléctrico, sin contenedor tipo botón."""
    horizontal = read_svg(LOGO_HORIZONTAL) or _FALLBACK_LOGO
    horizontal = horizontal.replace('fill="#16181D"', 'fill="#365CF5"')
    return (
        '<div class="salva-header-brand">'
        f'<div class="logo-wrap logo-horizontal">{horizontal}</div>'
        "</div>"
    )


def symbol_white_html(size: int = 28) -> str:
    svg = read_svg(SYMBOL_WHITE)
    if not svg:
        return _FALLBACK_SYMBOL.replace("#365CF5", "#FFFFFF")
    return svg.replace('width="32"', f'width="{size}"').replace('height="32"', f'height="{size}"')


def _draw_symbol_png(path: Path) -> bool:
    """Genera salva-symbol.png desde el diseño del símbolo SALVA."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Casa (azul #365CF5) — coordenadas escaladas desde viewBox 32x32
        scale = size / 32
        house = [
            (16 * scale, 4 * scale),
            (26 * scale, 12 * scale),
            (26 * scale, 26 * scale),
            (18 * scale, 26 * scale),
            (18 * scale, 19 * scale),
            (14 * scale, 19 * scale),
            (14 * scale, 26 * scale),
            (6 * scale, 26 * scale),
            (6 * scale, 12 * scale),
        ]
        draw.line(house + [house[0]], fill="#365CF5", width=max(2, int(2 * scale)), joint="curve")

        # Check verde (#18A875)
        check = [
            (22 * scale, 8 * scale),
            (24.5 * scale, 10.5 * scale),
            (28 * scale, 7 * scale),
        ]
        draw.line(check, fill="#18A875", width=max(2, int(2 * scale)), joint="curve")

        img.save(path, format="PNG")
        return path.is_file()
    except OSError:
        return False


def _symbol_png_path() -> Path | None:
    if SYMBOL_PNG.is_file():
        return SYMBOL_PNG
    if _draw_symbol_png(SYMBOL_PNG):
        return SYMBOL_PNG
    return None


def page_icon():
    """Icono válido para st.set_page_config. Prefiere assets/salva-symbol.png."""
    png = _symbol_png_path()
    if png is not None:
        try:
            from PIL import Image

            return Image.open(png)
        except Exception:
            return str(png.resolve())
    return "🏠"
