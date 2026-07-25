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
    get_balance,
    load_transactions,
    receipt_html,
    transfer,
    unassigned_savings,
)
from services.bookings import appointment_label, list_bookings
from services.formatting import format_ars
from services.goals import assign_from_ahorro, create_goal, load_goals, primary_goal
from services.home_history import filter_history, history_summary, load_history
from services.navigation import go, start_service
from services.planner import add_manual_task
from services.predict import generate_recommendations, load_profile, narrative_phrases, predict_intro, save_profile
from services.pro_photos import render_pro_avatar
from services.professionals import SERVICE_TYPES, get_professional
from services.salvita import salvita_html
from services.service_characters import SERVICE_ICON_KEY, character_image_path
from services.ui_components import empty_state


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
    profile = load_profile() or {}
    bookings = list_bookings()
    active_statuses = ["Turno reservado", "Reserva confirmada", "En seguimiento", "Confirmada", "En curso"]
    upcoming = bookings[bookings["booking_status"].isin(active_statuses)] if not bookings.empty else bookings
    status, reason = _home_status(recs, upcoming, hist)

    st.markdown(
        '<h2 class="mh-hero-title">Tu hogar, organizado con SALVA.</h2>'
        '<p class="body-text">Consultá tus saldos, prepará proyectos, anticipá mantenimientos '
        "y revisá todo lo que pasó en tu hogar.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="sim-banner">{SIM_DISCLAIMER}</div>', unsafe_allow_html=True)

    # A — Resumen del hogar
    _scroll_anchor("resumen")
    st.markdown("### Así está tu hogar")
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(salvita_html("neutral", ""), unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{profile.get('home_type', 'Mi departamento')}**")
            st.caption(
                f"{profile.get('neighborhood', 'Buenos Aires')} · "
                f"{profile.get('home_type', 'Departamento')} · "
                f"{profile.get('age_years', '10')} años aprox."
            )
            st.markdown(f"**Estado general:** {status}")
            st.caption(reason)
            if not upcoming.empty:
                u = upcoming.iloc[0]
                st.caption(f"**Próximo servicio:** {u['service_type']} · {appointment_label(u.to_dict())}")
            if hist["total"]:
                last = load_history().iloc[0]
                st.caption(f"**Garantía activa:** {last.get('guarantee_status', 'Vigente')}")
        st.metric("Fondos totales del hogar", format_ars(summary["total"]))
        st.caption(f"SALVA Cuenta + SALVA Ahorro = {format_ars(summary['cuenta'])} + {format_ars(summary['ahorro'])}")

    # B — Resumen financiero
    _scroll_anchor("finanzas")
    st.markdown("### Resumen financiero")
    fc1, fc2 = st.columns(2)
    with fc1:
        with st.container(border=True):
            st.markdown("**SALVA Cuenta**")
            st.markdown(f"### {format_ars(summary['cuenta'])}")
            st.caption("Saldo disponible para pagar servicios.")
            if not upcoming.empty:
                u = upcoming.iloc[0]
                st.caption(f"Próximo pago: {u.get('service_type', '—')}")
            st.caption(f"Alias de muestra: `{SIM_ALIAS}`")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Fondear cuenta", key="mh_fund_btn", use_container_width=True):
                    st.session_state.mh_show_funding = True
            with b2:
                if st.button("Ver movimientos", key="mh_mov_cuenta", use_container_width=True):
                    st.session_state.mh_mov_filter = "SALVA Cuenta"
                    st.session_state.mh_scroll_mov = True
    with fc2:
        with st.container(border=True):
            st.markdown("**SALVA Ahorro**")
            st.markdown(f"### {format_ars(summary['ahorro'])}")
            st.caption(f"No asignado: {format_ars(summary['unassigned'])}")
            st.caption(f"Asignado a objetivos: {format_ars(summary['assigned'])}")
            if goal:
                st.caption(f"Objetivo principal: {goal['name']}")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Mover dinero", key="mh_transfer_btn", use_container_width=True):
                    st.session_state.mh_show_transfer = True
            with b2:
                if st.button("Ver objetivos", key="mh_goals_btn", use_container_width=True):
                    st.session_state.mh_scroll_goals = True

    if st.session_state.get("mh_show_funding"):
        _render_funding(summary)

    if st.session_state.get("mh_show_transfer"):
        _render_transfers(summary)

    # C — Movimientos internos (siempre visible resumido)
    _scroll_anchor("transferencias")
    st.markdown("### Mover dinero dentro de SALVA")
    st.caption("Solo entre SALVA Cuenta y SALVA Ahorro.")
    if not st.session_state.get("mh_show_transfer"):
        if st.button("Abrir transferencias", key="mh_open_xfer"):
            st.session_state.mh_show_transfer = True
            st.rerun()

    # D — Objetivos y proyectos
    _scroll_anchor("objetivos")
    st.markdown("### Objetivos y proyectos sugeridos")
    _render_projects_row(goal, recs, summary)
    _render_goals(summary)

    # E — SALVA Predict
    _scroll_anchor("predict")
    st.markdown("### SALVA Predict")
    _render_predict(recs, profile, summary)

    # F — Historial
    _scroll_anchor("historial")
    st.markdown("### Historial de servicios")
    _render_history_preview(hist)

    # G — Movimientos monetarios
    _scroll_anchor("movimientos")
    st.markdown("### Movimientos monetarios")
    _render_movements()


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
    with st.expander("Perfil del hogar"):
        with st.form("home_profile_unified"):
            c1, c2 = st.columns(2)
            with c1:
                ht = st.selectbox("Tipo", ["Departamento", "Casa", "PH"])
                age = st.number_input("Antigüedad (años)", 0, 100, int(profile.get("age_years") or 10) if profile else 10)
            with c2:
                hood = st.text_input("Ubicación", value=profile.get("neighborhood", "Palermo") if profile else "Palermo")
                gas = st.checkbox("Tiene gas", value=str(profile.get("has_gas", "true")).lower() == "true" if profile else True)
                ac = st.checkbox("Tiene aire acondicionado", value=str(profile.get("has_ac", "false")).lower() == "true" if profile else False)
            if st.form_submit_button("Guardar perfil", use_container_width=True):
                save_profile(ht, age, 3, gas, ac, 2020, hood)
                st.success("Perfil guardado.")
                st.rerun()
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
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                if st.button("Buscar profesional", key=f"pred_pro_{rec['title'][:12]}", use_container_width=True):
                    start_service("Mantenimiento general")
            with a2:
                if st.button("Crear objetivo", key=f"pred_goal_{rec['title'][:12]}", use_container_width=True):
                    st.session_state.mh_scroll_goals = True
                    st.rerun()
            with a3:
                if st.button("Agregar al plan", key=f"pred_plan_{rec['title'][:12]}", use_container_width=True):
                    add_manual_task(rec["title"], rec["reason"], "Este mes", (rec["cost_low"] + rec["cost_high"]) / 2, rec["suggested_date"])
                    st.success("Agregado al plan.")
            with a4:
                if st.button("No me interesa por ahora", key=f"pred_skip_{rec['title'][:12]}", use_container_width=True):
                    st.caption("Entendido. Podés revisarlo más adelante.")


def _render_history_preview(hist) -> None:
    df = load_history()
    if df.empty:
        if empty_state("libreta", "Tu historial está listo", "Acá guardamos la historia de tu hogar.", "Buscar profesionales", "mh_empty_hist", salvita_state="neutral"):
            start_service()
        return
    for _, row in df.head(3).iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([1, 5])
            with c1:
                path = character_image_path(SERVICE_ICON_KEY.get(row["service_category"], "todos"))
                if path:
                    st.image(str(path), width=36)
            with c2:
                st.markdown(f"**{row['service_category']}** · {row['date']}")
                pro = None
                for pid in [f"PRO{i:03d}" for i in range(1, 17)]:
                    p = get_professional(pid)
                    if p and p.get("name") == row["professional_name"]:
                        pro = p
                        break
                if pro:
                    cc1, cc2 = st.columns([1, 5])
                    with cc1:
                        render_pro_avatar(pro, 36)
                    with cc2:
                        st.caption(row["professional_name"])
                st.caption(row.get("work_completed", row.get("reported_problem", "")))
                st.caption(f"{format_ars(row['final_price'])} · {row['rating']}/5 · {row['guarantee_status']}")
    if hist["total"] > 3:
        st.caption(f"Mostrando 3 de {hist['total']} servicios completados.")


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
