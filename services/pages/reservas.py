"""Mis reservas."""

import streamlit as st

from services.bookings import (
    PAYMENT_CONFIRMED,
    appointment_label,
    flow_step_for_booking,
    get_booking,
    list_bookings,
)
from services.formatting import format_ars
from services.navigation import start_service
from services.professionals import get_professional
from services.ui_components import empty_state, render_chat_panel


def open_booking_in_services(booking: dict) -> None:
    """Reingresa al flujo transaccional sin duplicar su lógica."""
    st.session_state.active_booking_id = booking["id"]
    st.session_state.created_booking_id = booking["id"]
    st.session_state.pending_payment_booking_id = booking["id"]
    st.session_state.flow_step = flow_step_for_booking(booking)
    st.session_state.section = "Servicios"
    st.rerun()


def open_booking_chat(booking_id: str) -> None:
    st.session_state.chat_booking_id = booking_id
    st.session_state.show_chat_res = booking_id
    st.rerun()


def render() -> None:
    st.markdown('<p class="section-title">Mis reservas</p>', unsafe_allow_html=True)
    name = st.text_input("Buscar por tu nombre", placeholder="María López", key="res_search")
    bookings = list_bookings(name.strip()) if name.strip() else list_bookings()

    if bookings.empty:
        if empty_state(
            "reservas",
            "Todavía no tenés reservas",
            "Cuando solicites un servicio, vas a poder seguirlo desde acá.",
            "Solicitar un servicio",
            "empty_res",
            salvita_state="neutral",
        ):
            start_service()
        return

    for _, b in bookings.iterrows():
        with st.container(border=True):
            st.markdown(f"**{b['id']}** · {b['service_type']} · {b.get('booking_status', '—')}")
            st.caption(f"{b['professional_name']} · {format_ars(b.get('approved_price') or b.get('initial_price'))} · {b.get('payment_status', '—')}")
            st.caption(f"Estado: {b.get('service_status', '—')} · {appointment_label(b.to_dict())}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Ver seguimiento", key=f"trk_{b['id']}", use_container_width=True):
                    open_booking_in_services(b.to_dict())
            with c2:
                if str(b.get("chat_enabled", "")).lower() in ("true", "1", "yes") or b.get("payment_status") == PAYMENT_CONFIRMED:
                    if st.button("Chatear con el profesional", key=f"chat_{b['id']}", use_container_width=True):
                        open_booking_chat(b["id"])
            if st.session_state.get("show_chat_res") == b["id"]:
                booking = get_booking(b["id"])
                pro = get_professional(b["professional_id"]) or {}
                if booking:
                    render_chat_panel(booking, pro)
