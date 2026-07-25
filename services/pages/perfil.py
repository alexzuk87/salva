"""Perfil del usuario."""

import streamlit as st

from services.bookings import list_bookings
from services.complaints import list_complaints
from services.goals import load_goals
from services.home_history import history_summary
from services.navigation import SIM_NOTE


def render() -> None:
    st.markdown('<p class="section-title">Tu perfil</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        first_name = st.text_input(
            "Nombre",
            value=st.session_state.get("profile_first_name", ""),
            key="profile_first_name_input",
        )
    with c2:
        last_name = st.text_input(
            "Apellido",
            value=st.session_state.get("profile_last_name", ""),
            key="profile_last_name_input",
        )
    if first_name != st.session_state.get("profile_first_name"):
        st.session_state.profile_first_name = first_name.strip()
    if last_name != st.session_state.get("profile_last_name"):
        st.session_state.profile_last_name = last_name.strip()
    full_name = f"{first_name} {last_name}".strip()
    st.markdown('<div class="salva-card">', unsafe_allow_html=True)
    hist = history_summary()
    bookings = list_bookings(full_name) if full_name else list_bookings()
    goals = load_goals()
    complaints = list_complaints()
    st.markdown(f"**Servicios completados:** {hist['total']}")
    st.markdown(f"**Reservas:** {len(bookings)}")
    st.markdown(f"**Objetivos de ahorro:** {len(goals)}")
    st.markdown(f"**Reclamos:** {len(complaints)}")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sim-banner">{SIM_NOTE}</div>', unsafe_allow_html=True)
