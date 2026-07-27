"""Perfil del usuario."""

import streamlit as st

from services.bookings import list_bookings
from services.complaints import list_complaints
from services.goals import load_goals
from services.home_history import history_summary
from services.locations import PROVINCES
from services.navigation import SIM_NOTE
from services.predict import load_profile, save_profile


def profile_with_booking_fallback(profile: dict | None = None) -> dict:
    """Completa dirección desde la última reserva sin crear otra fuente de datos."""
    result = dict(profile or load_profile() or {})
    full_name = " ".join(
        p for p in [
            result.get("first_name") or st.session_state.get("profile_first_name", ""),
            result.get("last_name") or st.session_state.get("profile_last_name", ""),
        ] if p
    ).strip()
    bookings = list_bookings(full_name) if full_name else list_bookings()
    if not bookings.empty:
        latest = bookings.iloc[0]
        for field in ("province", "locality", "neighborhood", "address"):
            if not result.get(field):
                result[field] = latest.get(field, "")
    return result


def render_profile_editor(profile: dict | None = None, key_prefix: str = "profile") -> None:
    profile = profile_with_booking_fallback(profile)
    province = profile.get("province") or "Ciudad Autónoma de Buenos Aires"
    province_index = PROVINCES.index(province) if province in PROVINCES else 0
    with st.form(f"{key_prefix}_editor"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Nombre", value=profile.get("first_name") or st.session_state.get("profile_first_name", ""))
            home_type = st.selectbox(
                "Tipo de vivienda",
                ["Departamento", "Casa", "PH"],
                index=["Departamento", "Casa", "PH"].index(profile.get("home_type")) if profile.get("home_type") in ["Departamento", "Casa", "PH"] else 0,
            )
            selected_province = st.selectbox("Provincia", PROVINCES, index=province_index)
        with c2:
            last_name = st.text_input("Apellido", value=profile.get("last_name") or st.session_state.get("profile_last_name", ""))
            locality = st.text_input("Localidad", value=profile.get("locality", ""))
            address = st.text_input("Dirección principal", value=profile.get("address", ""))
        if st.form_submit_button("Guardar perfil", type="primary", use_container_width=True):
            st.session_state.profile_first_name = first_name.strip()
            st.session_state.profile_last_name = last_name.strip()
            save_profile(
                home_type,
                int(profile.get("age_years") or 10),
                int(profile.get("rooms") or 3),
                str(profile.get("has_gas", "true")).lower() in ("true", "1", "yes"),
                str(profile.get("has_ac", "false")).lower() in ("true", "1", "yes"),
                int(profile.get("last_electrical_review") or 2020),
                profile.get("neighborhood") or locality,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                province=selected_province,
                locality=locality.strip(),
                address=address.strip(),
            )
            st.success("Perfil actualizado.")
            st.rerun()


def render() -> None:
    st.markdown('<p class="section-title">Tu perfil</p>', unsafe_allow_html=True)
    profile = profile_with_booking_fallback()
    render_profile_editor(profile)
    full_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
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
