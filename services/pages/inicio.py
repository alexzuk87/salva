"""Página de inicio — landing premium."""

import streamlit as st

from services.bookings import list_bookings
from services.formatting import format_ars
from services.goals import primary_goal
from services.home_history import history_summary
from services.navigation import start_service
from services.predict import generate_recommendations
from services.professionals import recommend_professionals
from services.reviews import get_reviews_for_professional
from services.salvita import salvita_html
from services.ui_components import (
    benefit_cards,
    category_selector,
    hero_visual_composition,
    pro_card_html,
    review_html,
)


def render() -> None:
    st.markdown(salvita_html("neutral", "¿Qué resolvemos hoy?"), unsafe_allow_html=True)
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<span class="hero-badge">Servicios del hogar con respaldo</span>', unsafe_allow_html=True)
        st.markdown(
            '<h1 class="hero-title">Tu hogar, en <span class="accent">buenas manos</span>.</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="body-text">Encontrá profesionales verificados, reservá un turno exacto y resolvé '
            "lo que necesitás con precio claro y garantía SALVA.</p>",
            unsafe_allow_html=True,
        )
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("Solicitar un servicio", type="primary", use_container_width=True, key="hero_cta"):
                start_service()
        with bc2:
            if st.button("Ver cómo funciona", use_container_width=True, key="hero_how"):
                st.session_state.show_how_it_works = not st.session_state.get("show_how_it_works")
                st.rerun()
        st.markdown(
            '<p class="trust-row">Identidad verificada · Pago seguro · Garantía post-servicio</p>',
            unsafe_allow_html=True,
        )
    with right:
        hero_visual_composition()

    if st.session_state.get("show_how_it_works"):
        with st.container(border=True):
            st.markdown("#### Cómo funciona SALVA")
            st.markdown(
                "1. Contanos qué pasó · 2. Elegí un profesional verificado · "
                "3. Confirmá precio y turno · 4. Pagá de forma simulada · "
                "5. Seguí el servicio · 6. Calificá y guardalo en SALVA Historial"
            )

    selected = category_selector("home_cat")
    if selected == "__all__":
        start_service()
    elif selected:
        start_service(selected)

    benefit_cards()

    st.markdown('<p class="section-title">Así está tu hogar hoy</p>', unsafe_allow_html=True)
    from services.accounts import account_summary
    from services.navigation import go as nav_go
    mh = account_summary()
    hist = history_summary()
    goal = primary_goal()
    recs = generate_recommendations()
    bookings = list_bookings()
    active_statuses = ["Turno reservado", "Reserva confirmada", "En seguimiento", "Confirmada", "En curso"]
    upcoming = bookings[bookings["booking_status"].isin(active_statuses)] if not bookings.empty else bookings
    mc1, mc2 = st.columns([2, 1])
    with mc1:
        goal_line = "—"
        goal_pct = ""
        if goal:
            saved = float(goal.get("saved_amount") or 0)
            target = float(goal.get("target_amount") or 1)
            goal_line = goal["name"]
            goal_pct = f" ({saved / target * 100:.0f}%)"
        predict_line = recs[0]["title"] if recs else "—"
        if not upcoming.empty:
            u = upcoming.iloc[0]
            service_line = f"Próximo: {u['service_type']} · {u.get('appointment_date', '—')}"
        elif hist["total"]:
            service_line = f"Último completado: {hist['last_date']}"
        else:
            service_line = "Sin servicios activos"
        st.markdown(
            f'<div class="mh-preview salva-card">'
            f'<p><strong>SALVA Cuenta:</strong> {format_ars(mh["cuenta"])}</p>'
            f'<p><strong>SALVA Ahorro:</strong> {format_ars(mh["ahorro"])}</p>'
            f'<p><strong>Objetivo principal:</strong> {goal_line}{goal_pct}</p>'
            f'<p><strong>SALVA Predict:</strong> {predict_line}</p>'
            f'<p><strong>Servicios:</strong> {service_line}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("Ver Mi hogar", type="primary", use_container_width=True, key="go_mihogar"):
                nav_go("Mi hogar")
        with bc2:
            if st.button("Fondear SALVA Cuenta", use_container_width=True, key="go_fund"):
                st.session_state.mh_show_funding = True
                nav_go("Mi hogar")
        with bc3:
            if st.button("Crear objetivo", use_container_width=True, key="go_objetivo"):
                st.session_state.mh_scroll_goals = True
                nav_go("Mi hogar")
    with mc2:
        st.markdown(salvita_html("neutral", "SALVA te salva — organizá tu hogar en un solo lugar."), unsafe_allow_html=True)

    st.markdown('<p class="section-title">Profesionales destacados</p>', unsafe_allow_html=True)
    df = recommend_professionals("Plomería", "Programado", "09:00", province="Ciudad Autónoma de Buenos Aires", locality="Ciudad Autónoma de Buenos Aires").head(2)
    if df.empty:
        st.caption("Explorá categorías para ver profesionales.")
    else:
        for _, pro in df.iterrows():
            pro_d = pro.to_dict()
            revs = get_reviews_for_professional(pro["id"], 1)
            rh = "".join(
                review_html(r["customer_name"], r["rating"], r["comment"], r.get("neighborhood", ""))
                for _, r in revs.iterrows()
            )
            st.markdown(
                pro_card_html(pro_d, "tu zona", int(pro["neighborhood_jobs"]), pro["eta_label"], float(pro["estimated_price"]), rh),
                unsafe_allow_html=True,
            )

    st.markdown('<p class="section-title">El estado de tu hogar</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    bookings = list_bookings()
    if not bookings.empty and "booking_status" in bookings.columns:
        upcoming = bookings[bookings["booking_status"].isin(["Confirmada", "Pendiente", "En curso"])]
    else:
        upcoming = bookings.iloc[0:0]
    hist = history_summary()
    goal = primary_goal()
    recs = generate_recommendations()

    with c1:
        if not upcoming.empty:
            u = upcoming.iloc[0]
            st.metric("Próximo servicio", u["service_type"])
            st.caption(u.get("appointment_date") or u.get("preferred_date", "—"))
        else:
            st.metric("Próximo servicio", "—")
            st.caption("Sin reservas activas")
    with c2:
        st.metric("Último mantenimiento", hist["last_date"])
    with c3:
        if goal:
            saved = float(goal.get("saved_amount") or 0)
            st.metric("Objetivo activo", goal["name"][:18])
            st.caption(format_ars(saved))
        else:
            st.metric("Objetivo activo", "—")
            st.caption("Creá uno en Mi hogar")
    with c4:
        nxt = recs[0]["title"][:22] if recs else "—"
        st.metric("Próximo mantenimiento", nxt)
        if recs:
            st.caption(recs[0]["priority"])

    st.markdown(
        '<div class="sim-banner">Prototipo académico SALVA — datos y verificaciones simuladas.</div>',
        unsafe_allow_html=True,
    )
