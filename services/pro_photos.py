"""Fotos profesionales — rutas seguras, fallback e auditoría."""

from __future__ import annotations

import base64
import html
import logging
from pathlib import Path

import streamlit as st

from services.branding import PROJECT_ROOT

PHOTO_DIR = PROJECT_ROOT / "assets" / "professionals"
logger = logging.getLogger("salva.photos")


def photo_path(pro_id: str, photo_url: str = "") -> Path | None:
    """Resuelve ruta local predecible (repo root, multiplataforma)."""
    if photo_url:
        rel = photo_url.replace("\\", "/").lstrip("/")
        if rel.startswith("assets/professionals/"):
            candidate = PROJECT_ROOT / rel
            if candidate.is_file():
                return candidate
    pid = str(pro_id or "").strip().lower()
    if pid:
        for name in (f"{pid}.jpg", f"{pid}.jpeg", f"{pid}.png"):
            candidate = PHOTO_DIR / name
            if candidate.is_file():
                return candidate
    return None


def initials(name: str) -> str:
    parts = [p for p in str(name or "?").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def fallback_avatar_html(name: str, size: int = 72) -> str:
    ini = html.escape(initials(name))
    return (
        f'<div class="avatar-fallback" style="width:{size}px;height:{size}px;'
        f'font-size:{max(12, size // 3)}px" aria-hidden="true">{ini}</div>'
    )


def photo_to_data_uri(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(suffix, "application/octet-stream")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def avatar_img_html(pro: dict, size: int = 72) -> str:
    """HTML seguro para tarjetas/comprobantes. Sin texto alt visible."""
    name = str(pro.get("name", "Profesional"))
    path = photo_path(str(pro.get("id", "")), str(pro.get("photo_url", "")))
    if path and path.is_file():
        uri = photo_to_data_uri(path)
        return (
            f'<div class="pro-photo-wrap" style="width:{size}px;height:{size}px">'
            f'<img class="pro-photo" src="{uri}" width="{size}" height="{size}" alt="" '
            f'role="presentation" loading="lazy"/></div>'
        )
    return f'<div class="pro-photo-wrap" style="width:{size}px;height:{size}px">{fallback_avatar_html(name, size)}</div>'


def render_pro_avatar(pro: dict, size: int = 72) -> None:
    """Componente Streamlit nativo con fallback a iniciales."""
    name = str(pro.get("name", "Profesional"))
    path = photo_path(str(pro.get("id", "")), str(pro.get("photo_url", "")))
    if path and path.is_file():
        st.image(str(path.resolve()), width=size)
    else:
        st.markdown(fallback_avatar_html(name, size), unsafe_allow_html=True)


def audit_professional_photos(pros_df) -> list[str]:
    """Devuelve lista de IDs con foto faltante. Registra en log de desarrollo."""
    missing: list[str] = []
    for _, row in pros_df.iterrows():
        pid = str(row.get("id", ""))
        path = photo_path(pid, str(row.get("photo_url", "")))
        if not path:
            missing.append(pid)
            logger.warning("Foto profesional faltante: %s (%s)", pid, row.get("name", ""))
    return missing


def ensure_photo_dir() -> None:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
