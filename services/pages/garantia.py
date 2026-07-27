"""Garantía SALVA."""

import streamlit as st

from services.bookings import update_booking
from services.complaints import CATEGORIES, create_complaint, list_complaints


def render_complaint_form(prefill_booking_id: str = "", key_prefix: str = "guarantee") -> None:
    with st.form(f"{key_prefix}_complaint"):
        bid = st.text_input(
            "Número de reserva",
            value=prefill_booking_id,
            placeholder="BK001",
            disabled=bool(prefill_booking_id),
        )
        cat = st.selectbox("Categoría", CATEGORIES)
        desc = st.text_area("Descripción")
        resolution = st.text_input("Resolución solicitada")
        st.caption("Evidencia opcional: podés adjuntar una imagen")
        evidence = st.file_uploader("Seleccionar imagen", type=["jpg", "png"], label_visibility="collapsed")
        if st.form_submit_button("Iniciar reclamo", type="primary", use_container_width=True):
            if bid.strip() and desc.strip():
                note = evidence.name if evidence else ""
                row = create_complaint(bid.strip().upper(), cat, desc.strip(), resolution.strip(), note)
                update_booking(bid.strip().upper(), guarantee_status="Reclamo iniciado")
                st.success(f"Reclamo {row['id']} — Estado: Reclamo iniciado")
            else:
                st.error("Completá reserva y descripción.")


def render_complaints_list(booking_id: str | None = None) -> None:
    complaints = list_complaints(booking_id)
    if not complaints.empty:
        st.markdown("**Reclamos existentes**")
        for _, c in complaints.iterrows():
            st.markdown(f"**{c['id']}** · {c['booking_id']} · {c['category']} · _{c['status']}_")


def render() -> None:
    st.markdown('<p class="section-title">Tu servicio tiene respaldo</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="body-text">Si el trabajo no coincide con lo acordado o presenta una falla relacionada, '
        "podés iniciar un reclamo desde SALVA. Revisaremos la información y te acompañaremos en la resolución.</p>",
        unsafe_allow_html=True,
    )
    st.caption("Canal formal de reclamo. No implica reembolso automático.")
    with st.container(border=True):
        render_complaint_form()
    render_complaints_list()
