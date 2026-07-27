"""Navegación principal SALVA — única fuente de verdad."""

import streamlit as st

from services.branding import logo_header_html

MAIN_NAV = [
    "Inicio",
    "Servicios",
    "Mi hogar",
]
ROUTABLE_SECTIONS = MAIN_NAV + ["Reservas", "Pagos", "Garantía", "Perfil"]
SECTION_PARENT = {
    "Reservas": "Servicios",
    "Garantía": "Servicios",
    "Pagos": "Mi hogar",
    "Perfil": "Mi hogar",
}

SIM_NOTE = "Información simulada para este prototipo académico."


def init_state() -> None:
    defaults = {
        "section": "Inicio",
        "flow_step": 1,
        "form_step": 1,
        "request": {},
        "diagnosis": None,
        "selected_pro_id": None,
        "view_pro_id": None,
        "sort_filter": "Mejor calificados",
        "created_booking_id": None,
        "pending_payment_booking_id": None,
        "active_booking_id": None,
        "upload_meta": "",
        "preset_service": "",
        "show_how_it_works": False,
        "loading_match": False,
        "show_booking_receipt": False,
        "show_payment_receipt": False,
        "show_chat": False,
        "chat_booking_id": None,
        "profile_first_name": "",
        "profile_last_name": "",
        "fund_receipt": None,
        "transfer_receipt": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def go(section: str, **kwargs) -> None:
    if section not in ROUTABLE_SECTIONS:
        section = "Inicio"
    if st.session_state.get("section") != section:
        st.session_state.section = section
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


def clear_active_flow() -> None:
    """Limpia el flujo activo sin borrar reservas, historial ni transacciones."""
    st.session_state.flow_step = 1
    st.session_state.form_step = 1
    st.session_state.request = {}
    st.session_state.diagnosis = None
    st.session_state.selected_pro_id = None
    st.session_state.view_pro_id = None
    st.session_state.created_booking_id = None
    st.session_state.pending_payment_booking_id = None
    st.session_state.active_booking_id = None
    st.session_state.preset_service = ""
    st.session_state.show_booking_receipt = False
    st.session_state.show_payment_receipt = False
    st.session_state.show_chat = False


def start_service(preset: str = "", need: str = "") -> None:
    st.session_state.section = "Servicios"
    st.session_state.flow_step = 1
    st.session_state.form_step = 1
    st.session_state.request = {"description": need} if need else {}
    st.session_state.preset_service = preset
    st.session_state.selected_pro_id = None
    st.session_state.view_pro_id = None
    st.session_state.created_booking_id = None
    st.session_state.pending_payment_booking_id = None
    st.session_state.active_booking_id = None
    st.session_state.diagnosis = None
    st.session_state.show_booking_receipt = False
    st.session_state.show_payment_receipt = False
    st.session_state.show_chat = False
    st.rerun()


def _nav_button(label: str, key: str, active: bool) -> None:
    if st.button(
        label,
        key=key,
        use_container_width=True,
        type="primary" if active else "secondary",
    ):
        go(label)


def _nav_row(key_prefix: str, current: str, position: str) -> None:
    """Una sola fila de navegación — responsive vía CSS (sin duplicar widgets)."""
    with st.container():
        marker_class = "salva-nav-marker"
        if position == "bottom":
            marker_class += " salva-nav-bottom-marker"
        st.markdown(
            f'<span class="{marker_class}" aria-hidden="true"></span>',
            unsafe_allow_html=True,
        )
        cols = st.columns(len(MAIN_NAV))
        for col, label in zip(cols, MAIN_NAV):
            with col:
                _nav_button(label, f"{key_prefix}_{label}", current == label)


def render_main_navigation(position: str, key_prefix: str) -> None:
    """Navegación principal reutilizable. position: 'top' | 'bottom'"""
    current = st.session_state.get("section", "Inicio")
    current = SECTION_PARENT.get(current, current)
    if current not in MAIN_NAV:
        current = "Inicio"

    if position == "bottom":
        st.markdown('<div class="main-nav-bottom-sep"></div>', unsafe_allow_html=True)

    if position == "top":
        logo_col, nav_col = st.columns([1.15, 5.85])
        with logo_col:
            st.markdown(logo_header_html(), unsafe_allow_html=True)
            if st.button(
                "Inicio",
                key=f"{key_prefix}_logo_home",
                help="Volver al inicio",
            ):
                go("Inicio")
        with nav_col:
            _nav_row(key_prefix, current, position)
    else:
        _nav_row(key_prefix, current, position)
