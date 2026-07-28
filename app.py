"""SALVA — Marketplace premium de servicios para el hogar."""

import logging

import streamlit as st

from services import branding
from services.pro_photos import audit_professional_photos
from services.professionals import load_professionals
from services.ui_styles import MARKETPLACE_CSS

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="SALVA | Servicios para tu hogar",
    page_icon=branding.page_icon(),
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(MARKETPLACE_CSS, unsafe_allow_html=True)


def main() -> None:
    from services.auth import require_login

    if not require_login():
        return

    from services.data_store import ensure_all_csv_files
    from services.navigation import init_state, render_main_navigation
    from services.pages import garantia, inicio, mi_hogar, pagos, perfil, reservas, servicios

    ensure_all_csv_files()
    init_state()

    missing = audit_professional_photos(load_professionals())
    if missing and not st.session_state.get("_photo_warn_shown"):
        logging.warning("Fotos faltantes: %s", ", ".join(missing))
        st.session_state._photo_warn_shown = True

    render_main_navigation("top", "nav_top")

    section = st.session_state.section
    routers = {
        "Inicio": inicio.render,
        "Servicios": servicios.render,
        "Reservas": reservas.render,
        "Mi hogar": mi_hogar.render,
        "Pagos": pagos.render,
        "Garantía": garantia.render,
        "Perfil": perfil.render,
    }
    if section not in routers:
        st.session_state.section = "Inicio"
        section = "Inicio"
    routers[section]()
    render_main_navigation("bottom", "nav_bottom")


if __name__ == "__main__":
    main()
