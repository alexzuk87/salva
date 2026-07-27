"""Mi hogar — página unificada con saldos, objetivos, predict e historial."""

from datetime import date, timedelta

import streamlit as st

from services.accounts import (
    ACCOUNT_AHORRO,
    ACCOUNT_CUENTA,
    ALIAS_DISCLAIMER,
    FUNDING_EXPLANATION,
    SIM_ACCOUNT_HOLDER,
    SIM_ACCOUNT_ID,
    SIM_ACCOUNT_TYPE,
    SIM_ALIAS,
    SIM_DISCLAIMER,
    account_summary,
    deposit_cuenta,
    load_transactions,
    receipt_html,
    transfer,
)
from services.bookings import (
    PAYMENT_CONFIRMED,
    SERVICE_STATUS_FLOW,
    appointment_label,
    get_booking,
    list_bookings,
    split_bookings_for_home,
)
from services.formatting import format_ars
from services.goals import assign_from_ahorro, create_goal, load_goals, primary_goal
from services.home_history import history_summary, load_history
from services.navigation import start_service
from services.planner import add_manual_task, load_tasks
from services.predict import (
    generate_recommendations,
    load_profile,
    narrative_phrases,
    predict_intro,
    recommendation_service_type,
)
from services.professionals import SERVICE_TYPES, get_professional
from services.salvita import salvita_html
from services.salva_pay import payment_summary
from services.service_characters import SERVICE_ICON_KEY, character_image_path
from services.ui_components import (
    booking_receipt_html,
    render_chat_panel,
    tracking_road_html,
)
from services.pages.garantia import render_complaint_form, render_complaints_list
from services.pages.pagos import render_financing_simulator
from services.pages.perfil import profile_with_booking_fallback, render_profile_editor
from services.pages.reservas import open_booking_chat, open_booking_in_services


def _home_status(recs, upcoming, hist) -> tuple[str, str]:
    if not upcoming.empty and upcoming.iloc[0].get("booking_status") in ("Turno reservado", "En seguimiento"):
        return "Requiere atención", "Tenés un servicio pendiente o en curso."
    if recs and recs[0].get("priority") == "Alta":
        return "Mantenimiento próximo", recs[0]["title"]
    if hist["total"] == 0:
        return "Sin historial", "Todavía no registramos servicios completados."
    return "Todo al día", "Tu hogar está organizado y al día."


def _scroll_anchor(section_id: str) -> None:
    st.markdown(f'<div id="{section_id}" class="mh-anchor"></div>', unsafe_allow_html=True)


def render() -> None:
    summary = account_summary()
    goal = primary_goal()
    hist = history_summary()
    recs = generate_recommendations()
    profile = profile_with_booking_fallback(load_profile() or {})
    if profile.get("first_name") and not st.session_state.get("profile_first_name"):
        st.session_state.profile_first_name = profile["first_name"]
    if profile.get("last_name") and not st.session_state.get("profile_last_name"):
        st.session_state.profile_last_name = profile["last_name"]
    full_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
    bookings = list_bookings(full_name) if full_name else list_bookings()
    groups = split_bookings_for_home(bookings)
    active = groups["en_curso"]
    upcoming = groups["proximos"]
    status_source = active if not active.empty else upcoming
    status, reason = _home_status(recs, status_source, hist)

    st.markdown(
        '<h2 class="mh-hero-title">Tu hogar, organizado con SALVA.</h2>'
        '<p class="body-text">Gestioná servicios, dinero, objetivos, recomendaciones e historial '
        "desde un solo lugar.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="sim-banner">{SIM_DISCLAIMER}</div>', unsafe_allow_html=True)

    _render_profile_and_home(profile, status, reason)
    _render_next_section(active, upcoming, recs)
    _render_services_section(groups)
    _render_finances_section(summary, upcoming, goal)
    _render_projects_and_recommendations(goal, recs, profile, summary)


def _render_profile_and_home(profile: dict, status: str, reason: str) -> None:
    _scroll_anchor("perfil-vivienda")
    st.markdown("### Perfil y vivienda")
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        with c1:
            name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or "Completá tu nombre"
            location = ", ".join(
                p for p in [profile.get("address"), profile.get("locality"), profile.get("province")] if p
            ) or "Dirección principal pendiente"
            st.markdown(f'<p class="mh-profile-name">{name}</p>', unsafe_allow_html=True)
            st.caption(
                f"{profile.get('home_type') or 'Vivienda sin definir'} · "
                f"{profile.get('locality') or profile.get('neighborhood') or 'Localidad pendiente'}"
            )
            st.caption(location)
            st.markdown(f"**Estado general:** {status}")
            st.caption(reason)
        with c2:
            st.markdown(salvita_html("neutral", ""), unsafe_allow_html=True)
        with st.expander("Editar perfil"):
            render_profile_editor(profile, "mh_profile")


def _render_next_section(active, upcoming, recs) -> None:
    _scroll_anchor("lo-proximo")
    st.markdown("### Lo próximo")
    cards = st.columns(3)
    with cards[0]:
        with st.container(border=True):
            st.markdown("**Servicio en curso**")
            if active.empty:
                st.caption("No hay servicios en curso.")
                if st.button("Solicitar servicio", key="mh_next_start", use_container_width=True):
                    start_service()
            else:
                booking = active.iloc[0].to_dict()
                st.markdown(booking["service_type"])
                st.caption(f"{booking['professional_name']} · {booking.get('service_status', '—')}")
                if st.button("Ver seguimiento", key="mh_next_track", use_container_width=True):
                    open_booking_in_services(booking)
                if booking.get("payment_status") == PAYMENT_CONFIRMED and st.button(
                    "Abrir chat", key="mh_next_chat", use_container_width=True
                ):
                    st.session_state.mh_chat_location = "next"
                    open_booking_chat(booking["id"])
                if (
                    st.session_state.get("show_chat_res") == booking["id"]
                    and st.session_state.get("mh_chat_location") == "next"
                ):
                    with st.expander("Chat con el profesional", expanded=True):
                        render_chat_panel(
                            booking,
                            get_professional(booking.get("professional_id", "")) or {},
                        )
    with cards[1]:
        with st.container(border=True):
            st.markdown("**Próxima reserva**")
            if upcoming.empty:
                st.caption("No hay turnos pendientes.")
                if st.button("Solicitar servicio", key="mh_next_booking", use_container_width=True):
                    start_service()
            else:
                booking = upcoming.iloc[0].to_dict()
                st.markdown(booking["service_type"])
                st.caption(appointment_label(booking))
                if st.button("Continuar con el pago", key="mh_next_pay", use_container_width=True):
                    open_booking_in_services(booking)
    with cards[2]:
        with st.container(border=True):
            st.markdown("**Recomendación Predict**")
            if not recs:
                st.caption("Sin recomendaciones pendientes.")
            else:
                rec = recs[0]
                st.markdown(rec["title"])
                st.caption(f"{rec['priority']} · {rec['suggested_date']}")
                if st.button("Solicitar servicio", key="mh_next_predict", use_container_width=True):
                    start_service(recommendation_service_type(rec), rec["reason"])


def _render_services_section(groups: dict) -> None:
    _scroll_anchor("mis-servicios")
    st.markdown("### Mis servicios")
    in_progress_tab, upcoming_tab, history_tab = st.tabs(["En curso", "Próximos", "Historial"])
    with in_progress_tab:
        _render_booking_list(groups["en_curso"], "active")
    with upcoming_tab:
        _render_booking_list(groups["proximos"], "upcoming")
    with history_tab:
        _render_service_history(groups["finalizados"])


def _render_booking_list(bookings, key_prefix: str) -> None:
    if bookings.empty:
        st.caption("No hay servicios en esta categoría.")
        return
    for _, row in bookings.iterrows():
        booking = row.to_dict()
        with st.container(border=True):
            st.markdown(f"**{booking['service_type']}** · {booking['id']}")
            st.caption(
                f"{booking['professional_name']} · {appointment_label(booking)} · "
                f"{booking.get('payment_status', '—')}"
            )
            if key_prefix == "active":
                st.markdown(
                    tracking_road_html(
                        booking.get("service_status", ""),
                        SERVICE_STATUS_FLOW,
                        booking.get("service_type", ""),
                        get_professional(booking.get("professional_id", "")),
                    ),
                    unsafe_allow_html=True,
                )
            a1, a2 = st.columns(2)
            with a1:
                action = "Ver seguimiento" if key_prefix == "active" else "Continuar con el pago"
                if st.button(action, key=f"mh_{key_prefix}_open_{booking['id']}", use_container_width=True):
                    open_booking_in_services(booking)
            with a2:
                if booking.get("payment_status") == PAYMENT_CONFIRMED and st.button(
                    "Abrir chat", key=f"mh_{key_prefix}_chat_{booking['id']}", use_container_width=True
                ):
                    st.session_state.mh_chat_location = "next"
                    open_booking_chat(booking["id"])


def _render_service_history(finalized_bookings) -> None:
    history = load_history()
    if history.empty and finalized_bookings.empty:
        st.caption("Todavía no hay servicios finalizados.")
        return
    booking_map = {
        row["id"]: row.to_dict()
        for _, row in finalized_bookings.iterrows()
    }
    rows = history.sort_values("date", ascending=False).to_dict("records") if not history.empty else []
    known_ids = {row.get("booking_id") for row in rows}
    for booking_id, booking in booking_map.items():
        if booking_id not in known_ids:
            rows.append({
                "booking_id": booking_id,
                "date": booking.get("completed_at") or booking.get("appointment_date", ""),
                "service_category": booking.get("service_type", ""),
                "professional_name": booking.get("professional_name", ""),
                "final_price": booking.get("approved_price") or booking.get("initial_price", 0),
                "rating": "—",
                "guarantee_status": booking.get("guarantee_status", "Sin reclamo"),
                "work_completed": booking.get("work_completed", ""),
            })
    for row in rows:
        booking_id = row.get("booking_id", "")
        booking = get_booking(booking_id) or booking_map.get(booking_id)
        with st.container(border=True):
            st.markdown(f"**{row.get('service_category', 'Servicio')}** · {row.get('date', '—')}")
            st.caption(
                f"{row.get('professional_name', '—')} · {format_ars(row.get('final_price', 0))} · "
                f"Calificación: {row.get('rating', '—')}/5"
            )
            st.caption(f"Garantía SALVA: {row.get('guarantee_status', 'Sin reclamo')}")
            if row.get("work_completed"):
                st.caption(row["work_completed"])
            if booking:
                with st.expander("Ver comprobante"):
                    pro = get_professional(booking.get("professional_id", "")) or {}
                    st.markdown(
                        booking_receipt_html(
                            booking,
                            pro,
                            float(booking.get("approved_price") or booking.get("initial_price") or 0),
                            appointment_label(booking),
                            booking.get("location") or booking.get("address", ""),
                        ),
                        unsafe_allow_html=True,
                    )
            with st.expander("Iniciar reclamo con Garantía SALVA"):
                render_complaint_form(booking_id, f"mh_{booking_id}")
                render_complaints_list(booking_id)


def _render_finances_section(summary: dict, upcoming, goal) -> None:
    _scroll_anchor("finanzas")
    st.markdown("### Finanzas del hogar")
    pending = payment_summary()
    cards = st.columns(3)
    with cards[0]:
        with st.container(border=True):
            st.markdown("**SALVA Cuenta**")
            st.markdown(f"### {format_ars(summary['cuenta'])}")
            st.caption("Saldo disponible para pagar servicios.")
    with cards[1]:
        with st.container(border=True):
            st.markdown("**SALVA Ahorro**")
            st.markdown(f"### {format_ars(summary['ahorro'])}")
            st.caption(
                f"Libre: {format_ars(summary['unassigned'])} · "
                f"Objetivos: {format_ars(summary['assigned'])}"
            )
    with cards[2]:
        with st.container(border=True):
            st.markdown("**Próximo pago**")
            if upcoming.empty:
                st.markdown("### —")
                st.caption("Sin pagos pendientes.")
            else:
                booking = upcoming.iloc[0]
                st.markdown(f"### {format_ars(booking.get('approved_price') or booking.get('initial_price') or 0)}")
                st.caption(booking.get("service_type", "Servicio"))
            st.caption(f"{pending['pending_count']} pago(s) pendiente(s)")

    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Fondear SALVA Cuenta", key="mh_fund_btn", use_container_width=True):
            st.session_state.mh_show_funding = not st.session_state.get("mh_show_funding", False)
    with a2:
        if st.button("Mover dinero", key="mh_transfer_btn", use_container_width=True):
            st.session_state.mh_show_transfer = not st.session_state.get("mh_show_transfer", False)
    with a3:
        if st.button("Ver movimientos", key="mh_movements_btn", use_container_width=True):
            st.session_state.mh_show_movements = not st.session_state.get("mh_show_movements", False)
    a4, a5 = st.columns(2)
    with a4:
        if st.button("Ver objetivos", key="mh_goals_btn", use_container_width=True):
            st.session_state.mh_show_goals = not st.session_state.get("mh_show_goals", False)
    with a5:
        if st.button("Simular financiación", key="mh_finance_btn", use_container_width=True):
            st.session_state.mh_show_financing = not st.session_state.get("mh_show_financing", False)

    if st.session_state.get("mh_show_funding"):
        with st.expander("Fondear SALVA Cuenta", expanded=True):
            _render_funding(summary)
    if st.session_state.get("mh_show_transfer"):
        with st.expander("Mover dinero entre Cuenta y Ahorro", expanded=True):
            _render_transfers(summary)
    if st.session_state.get("mh_show_movements"):
        with st.expander("Movimientos monetarios", expanded=True):
            _render_movements()
    if st.session_state.get("mh_show_financing"):
        with st.expander("Simulación de financiación", expanded=True):
            render_financing_simulator("mh")


def _render_projects_and_recommendations(goal, recs, profile, summary) -> None:
    _scroll_anchor("proyectos")
    st.markdown("### Proyectos y recomendaciones")
    _render_projects_row(goal, recs, summary)
    if st.session_state.get("mh_show_goals"):
        with st.expander("SALVA Objetivos", expanded=True):
            _render_goals(summary)
    else:
        st.caption("Usá “Ver objetivos” en Finanzas del hogar para administrar fondos asignados.")
    st.markdown("#### SALVA Predict")
    _render_predict(recs, profile, summary)
    tasks = load_tasks()
    with st.expander("Plan de mantenimiento"):
        if tasks.empty:
            st.caption("Todavía no agregaste tareas al plan.")
        else:
            for _, task in tasks.head(8).iterrows():
                st.markdown(f"**{task['title']}** · {task['priority_bucket']}")
                st.caption(f"{task['recommended_date']} · {task['preparation_status']}")


def _render_funding(summary: dict) -> None:
    st.markdown("#### Fondear SALVA Cuenta")
    st.caption(FUNDING_EXPLANATION)
    with st.container(border=True):
        st.markdown(f"**Alias de muestra:** `{SIM_ALIAS}`")
        st.caption(ALIAS_DISCLAIMER)
        st.markdown(f"**Titular:** {SIM_ACCOUNT_HOLDER}")
        st.markdown(f"**Tipo:** {SIM_ACCOUNT_TYPE}")
        st.markdown(f"**Identificador simulado:** {SIM_ACCOUNT_ID}")
        if st.button("Copiar alias", key="copy_alias"):
            st.session_state["_alias_clip"] = SIM_ALIAS
            st.toast(f"Alias copiado: {SIM_ALIAS}")
        receipt = st.session_state.get("last_fund_receipt")
        if receipt:
            st.markdown(
                receipt_html(
                    {"transaction_id": receipt["transaction_id"], "description": "Ingreso simulado a SALVA Cuenta",
                     "amount": str(receipt["amount"]), "created_at": receipt["created_at"]},
                    receipt["balance"],
                    "Ingreso confirmado",
                ),
                unsafe_allow_html=True,
            )
            st.success(f"Saldo actualizado: {format_ars(receipt['balance'])}")
            return
        with st.form("fund_cuenta_form"):
            amount = st.number_input("Monto ($)", min_value=1000, max_value=5000000, value=10000, step=1000)
            confirm = st.checkbox("Confirmo el ingreso simulado desde una cuenta externa")
            submitted = st.form_submit_button("Confirmar ingreso", type="primary")
        if submitted:
            if not confirm:
                st.error("Marcá la confirmación para continuar.")
            elif amount <= 0:
                st.error("Ingresá un monto mayor a cero.")
            else:
                ok, msg, tx = deposit_cuenta(float(amount))
                if ok:
                    st.success("Ingreso registrado.")
                    st.rerun()
                else:
                    st.error(msg)


def _render_transfers(summary: dict) -> None:
    with st.container(border=True):
        direction = st.radio(
            "Operación",
            ["SALVA Cuenta → SALVA Ahorro", "SALVA Ahorro → SALVA Cuenta"],
            label_visibility="collapsed",
        )
        if direction.startswith("SALVA Cuenta"):
            source, dest = ACCOUNT_CUENTA, ACCOUNT_AHORRO
            available = summary["cuenta"]
        else:
            source, dest = ACCOUNT_AHORRO, ACCOUNT_CUENTA
            available = summary["unassigned"]
        st.markdown(f"**Origen:** {source.replace('_', ' ')} · Disponible: {format_ars(available)}")
        st.markdown(f"**Destino:** {dest.replace('_', ' ')}")
        with st.form("internal_transfer_form"):
            amount = st.number_input("Monto ($)", min_value=1000, max_value=5000000, value=3000, step=500)
            confirm = st.checkbox("Confirmo la transferencia simulada")
            submitted = st.form_submit_button("Confirmar transferencia", type="primary")
        if submitted:
            if not confirm:
                st.error("Marcá la confirmación para continuar.")
            elif amount <= 0:
                st.error("Ingresá un monto mayor a cero.")
            elif amount > available:
                st.error("El monto supera el saldo disponible en la cuenta origen.")
            else:
                ok, msg, tx = transfer(source, dest, float(amount), direction)
                if ok:
                    new_summary = account_summary()
                    st.markdown(receipt_html(tx, new_summary["cuenta"] if dest == ACCOUNT_CUENTA else new_summary["ahorro"], "Transferencia confirmada"), unsafe_allow_html=True)
                    st.success("Saldos actualizados.")
                    st.session_state.mh_show_transfer = False
                    st.rerun()
                else:
                    st.error(msg)


def _render_projects_row(goal, recs, summary) -> None:
    cols = st.columns(3)
    with cols[0]:
        with st.container(border=True):
            st.markdown("**Objetivo actual**")
            if goal:
                saved = float(goal.get("saved_amount") or 0)
                target = float(goal.get("target_amount") or 1)
                st.progress(min(saved / target, 1.0))
                st.caption(f"{goal['name']} · {format_ars(saved)} / {format_ars(target)}")
            else:
                st.caption("Sin objetivo activo")
    with cols[1]:
        with st.container(border=True):
            st.markdown("**Sugerencia Predict**")
            if recs:
                st.caption(recs[0]["title"])
                st.caption(f"{format_ars(recs[0]['cost_low'])} – {format_ars(recs[0]['cost_high'])}")
            else:
                st.caption("Sin sugerencias")
    with cols[2]:
        with st.container(border=True):
            st.markdown("**Preparación de ahorro**")
            if goal:
                need = max(float(goal.get("target_amount") or 0) - float(goal.get("saved_amount") or 0), 0)
                st.caption(f"Falta estimado: {format_ars(need)}")
            st.caption(f"Libre en Ahorro: {format_ars(summary['unassigned'])}")


def _render_goals(summary: dict) -> None:
    st.markdown("#### SALVA Objetivos")
    st.caption("Los objetivos son asignaciones dentro de SALVA Ahorro — no duplican el saldo total.")
    with st.expander("Crear nuevo objetivo"):
        with st.form("new_goal_unified", clear_on_submit=True):
            name = st.text_input("Nombre del objetivo", placeholder="Renovar el baño")
            cat = st.selectbox("Categoría", SERVICE_TYPES + ["Emergencias", "Remodelación"])
            target = st.number_input("Monto objetivo ($)", 10000, 5000000, 200000, 10000)
            tdate = st.date_input("Fecha objetivo", value=date.today() + timedelta(days=180))
            if st.form_submit_button("Crear objetivo", type="primary"):
                create_goal(name, cat, float(target), 0, tdate.isoformat(), 15000)
                st.success("Objetivo creado.")
                st.rerun()
    goals = load_goals()
    if goals.empty:
        st.info("Creá tu primer SALVA Objetivo.")
        return
    free = summary["unassigned"]
    for _, g in goals.iterrows():
        saved = float(g.get("saved_amount") or 0)
        target = float(g.get("target_amount") or 1)
        pct = min(saved / target * 100, 100)
        with st.container(border=True):
            st.markdown(f"**{g['name']}** · {g['category']}")
            st.progress(min(pct / 100, 1.0))
            st.caption(f"Asignado: {format_ars(saved)} · Meta: {format_ars(target)}")
            st.caption(f"Saldo libre en SALVA Ahorro: {format_ars(free)}")
            with st.form(f"goal_assign_{g['id']}"):
                amount = st.number_input("Monto a asignar ($)", 1000, 500000, 2000, 500, key=f"g_amt_{g['id']}")
                submitted = st.form_submit_button("Asignar ahorro al objetivo", type="primary")
            if submitted:
                ok, msg = assign_from_ahorro(g["id"], float(amount))
                if ok:
                    st.success("Asignación registrada.")
                    st.rerun()
                else:
                    st.error(msg)
                    if "no alcanza" in msg.lower():
                        if st.button("Ir a mover dinero", key=f"xfer_from_goal_{g['id']}"):
                            st.session_state.mh_show_transfer = True
                            st.rerun()


def _render_predict(recs, profile, summary) -> None:
    st.markdown(salvita_html("neutral", predict_intro()), unsafe_allow_html=True)
    for phrase in narrative_phrases(profile, load_history()):
        st.caption(f"· {phrase}")
    for rec in recs[:4]:
        char = character_image_path(SERVICE_ICON_KEY.get(rec.get("title", ""), "todos"))
        with st.container(border=True):
            c1, c2 = st.columns([1, 5])
            with c1:
                if char:
                    st.image(str(char), width=40)
            with c2:
                st.markdown(f"**{rec['title']}**")
                st.caption(rec["reason"])
                st.caption(f"**Cuándo:** {rec['suggested_date']} · **Costo estimado:** {format_ars(rec['cost_low'])} – {format_ars(rec['cost_high'])}")
                st.caption(f"Fondos disponibles: {format_ars(summary['unassigned'])} en Ahorro · {format_ars(summary['cuenta'])} en Cuenta")
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("Solicitar este servicio", key=f"pred_pro_{rec['title'][:12]}", use_container_width=True):
                    start_service(recommendation_service_type(rec), rec["reason"])
            with a2:
                if st.button("Crear objetivo", key=f"pred_goal_{rec['title'][:12]}", use_container_width=True):
                    st.session_state.mh_show_goals = True
                    st.rerun()
            with a3:
                if st.button("Agregar al plan", key=f"pred_plan_{rec['title'][:12]}", use_container_width=True):
                    tasks = load_tasks()
                    if not tasks.empty and rec["title"] in set(tasks["title"]):
                        st.info("Esta recomendación ya está en tu plan.")
                    else:
                        add_manual_task(
                            rec["title"],
                            rec["reason"],
                            "Este mes",
                            (rec["cost_low"] + rec["cost_high"]) / 2,
                            rec["suggested_date"],
                        )
                        st.success("Agregado al plan.")


def _render_movements() -> None:
    filt = st.session_state.get("mh_mov_filter", "Todos")
    filt = st.selectbox(
        "Filtrar",
        ["Todos", "SALVA Cuenta", "SALVA Ahorro", "Objetivos", "Pagos"],
        index=["Todos", "SALVA Cuenta", "SALVA Ahorro", "Objetivos", "Pagos"].index(filt) if filt in ["Todos", "SALVA Cuenta", "SALVA Ahorro", "Objetivos", "Pagos"] else 0,
        key="mh_mov_sel",
    )
    st.session_state.mh_mov_filter = filt
    txs = load_transactions(30)
    if txs.empty:
        st.caption("Sin movimientos registrados.")
        return
    for _, t in txs.iterrows():
        src = str(t.get("source_account", ""))
        dst = str(t.get("destination_account", ""))
        tx_type = str(t.get("transaction_type", ""))
        if filt == "SALVA Cuenta" and ACCOUNT_CUENTA not in (src, dst) and tx_type != "deposito":
            continue
        if filt == "SALVA Ahorro" and ACCOUNT_AHORRO not in (src, dst) and "ahorro" not in src:
            continue
        if filt == "Objetivos" and tx_type != "asignacion_objetivo":
            continue
        if filt == "Pagos" and tx_type != "pago_servicio":
            continue
        amt = float(t.get("amount") or 0)
        if tx_type in ("deposito",) or dst == ACCOUNT_CUENTA and src == "externo":
            sign, color = "+", "green"
        elif tx_type == "pago_servicio":
            sign, color = "−", "#8B2942"
        else:
            sign, color = "↔", "#365CF5"
        acct = dst if tx_type == "deposito" else (src if tx_type == "pago_servicio" else f"{src} → {dst}")
        st.markdown(
            f'<div class="mh-tx-row"><span style="color:{color};font-weight:700">{sign}{format_ars(amt)}</span> '
            f'<span>{t["created_at"]} · {t["description"]} · {acct} · Ref: {t["transaction_id"]}</span></div>',
            unsafe_allow_html=True,
        )
