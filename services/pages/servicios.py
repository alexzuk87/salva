"""Flujo de solicitud de servicio — 6 pasos."""

import time
from datetime import date

import streamlit as st

from services.auth import authenticated_user
from services.bookings import (
    PAYMENT_CONFIRMED,
    SERVICE_STATUS_FLOW,
    accept_price_change,
    advance_service_status,
    appointment_label,
    create_booking,
    get_booking,
    propose_price_change,
    update_booking,
)
from services.chat import add_system_message, seed_booking_chat
from services.diagnosis import build_diagnosis
from services.formatting import format_ars
from services.locations import PROVINCES, locality_options, location_summary
from services.navigation import clear_active_flow, go
from services.service_categories import category_internal, category_label as visible_category_label, resolve_selection
from services.service_guides import guide_for_category, render_category_guide
from services.ui_components import (
    booking_confirmed_receipt_html,
    booking_pending_receipt_html,
    booking_receipt_html,
    card_brands_html,
    completed_service_receipt_html,
    diagnosis_box_html,
    form_category_picker,
    payment_receipt_html,
    pro_card_html,
    render_chat_panel,
    render_flow_indicator,
    render_star_rating,
    review_html,
    service_icon_html,
    tracking_road_html,
)
from services.payments import (
    PAYMENT_METHODS, confirm_payment, detect_card_brand,
    sanitize_card_input, sanitize_cvv, sanitize_month, sanitize_year, validate_card,
)
from services.professionals import (
    BADGE_TOOLTIP,
    SERVICE_TYPES,
    estimate_arrival,
    estimate_price,
    get_professional,
    recommend_professionals,
    sort_professionals,
)
from services.ratings import get_rating, submit_completion
from services.reviews import get_reviews_for_professional
from services.scheduling import (
    ASAP, URGENCY_LEVELS, available_slots, format_appointment, grouped_slots,
    is_asap, min_appointment_date, slot_display,
)
from services.salvita import salvita_html
from services.ui_styles import FLOW_STEPS


def render() -> None:
    if st.session_state.flow_step == 1:
        render_flow_indicator(1, FLOW_STEPS)
        _form_wizard()
    else:
        render_flow_indicator(st.session_state.flow_step, FLOW_STEPS)
        {2: _profesionales, 3: _reserva, 4: _pago, 5: _seguimiento, 6: _finalizacion}.get(
            st.session_state.flow_step, _form_wizard
        )()


def _customer_name(req: dict | None = None) -> str:
    """Nombre visible del cliente desde Google; fallback a datos previos del request."""
    user = authenticated_user()
    if user.get("name"):
        return user["name"]
    req = req or st.session_state.get("request") or {}
    existing = str(req.get("customer_name", "")).strip()
    if existing:
        return existing
    fn = str(req.get("first_name", "")).strip()
    ln = str(req.get("last_name", "")).strip()
    return f"{fn} {ln}".strip() or "Cliente SALVA"


def _apply_authenticated_identity(req: dict) -> None:
    """Completa identidad del cliente sin pedir Nombre/Apellido en el formulario."""
    user = authenticated_user()
    req["customer_name"] = _customer_name(req)
    req["customer_email"] = user.get("email", "")
    req["customer_sub"] = user.get("sub", "")
    if user.get("name"):
        st.session_state.profile_first_name = user["name"]


def _go_to_professionals(req: dict) -> None:
    _apply_authenticated_identity(req)
    st.session_state.created_booking_id = None
    st.session_state.pending_payment_booking_id = None
    st.markdown(salvita_html("searching"), unsafe_allow_html=True)
    with st.spinner("Buscando profesionales verificados en tu zona..."):
        time.sleep(0.5)
        st.session_state.diagnosis = build_diagnosis(req)
    st.session_state.flow_step = 2
    st.session_state.form_step = 1
    st.rerun()


def _form_wizard() -> None:
    preset = st.session_state.get("preset_service", "")
    fs = st.session_state.form_step
    req = st.session_state.request
    _apply_authenticated_identity(req)

    if fs == 1:
        with st.container(border=True):
            st.markdown('<p class="form-step-num">¿Qué servicio necesitás?</p>', unsafe_allow_html=True)
            st.caption("Elegí un servicio y SALVA te ayuda con el resto.")
            if preset:
                st.info(f"Categoría sugerida: **{visible_category_label(preset) or preset}**")
            picked = form_category_picker("fs_cat")
            if picked:
                label, mapped = picked
                resolved = resolve_selection(label, mapped)
                req["category_key"] = resolved["key"]
                req["category_label"] = resolved["label"]
                req["service_type"] = resolved["internal"] or preset or req.get("service_type", SERVICE_TYPES[0])
                st.session_state.preset_service = req["service_type"]
                st.session_state.form_step = 2
                st.rerun()
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Atrás", key="fs1_back"):
                    go("Inicio")
            with c2:
                if st.button("Continuar →", type="primary", use_container_width=True, key="fs1_next"):
                    if not (preset or req.get("service_type") or req.get("category_label")):
                        st.error("Elegí una categoría de servicio.")
                    else:
                        resolved = resolve_selection(
                            req.get("category_label", ""),
                            preset or req.get("service_type", SERVICE_TYPES[0]),
                        )
                        req["category_key"] = resolved["key"]
                        req["category_label"] = resolved["label"] or visible_category_label(preset) or preset
                        req["service_type"] = resolved["internal"] or category_internal(preset) or preset
                        st.session_state.preset_service = req["service_type"]
                        st.session_state.form_step = 2
                        st.rerun()
        return

    category_ref = req.get("category_key") or req.get("category_label") or req.get("service_type") or preset
    category_label = req.get("category_label") or visible_category_label(category_ref) or category_ref
    svc = req.get("service_type") or category_internal(category_ref) or preset or SERVICE_TYPES[0]

    if fs == 2:
        guide = guide_for_category(req.get("category_key") or category_label)
        with st.container(border=True):
            st.markdown('<p class="form-step-num">Detalle del servicio</p>', unsafe_allow_html=True)
            st.markdown(f"**Categoría:** {category_label}", unsafe_allow_html=True)
            render_category_guide(req.get("category_key") or category_label)
            description = st.text_area(
                "Contanos qué necesitás resolver",
                value=req.get("description", ""),
                height=120,
                placeholder=str(guide["placeholder"]),
            )
            st.markdown("**Agregá fotos del problema (opcional)**")
            st.info(
                "Las fotos ayudan a evaluar mejor el trabajo, recibir una cotización más precisa "
                "y encontrar al profesional adecuado."
            )
            st.file_uploader(
                "Fotos del problema (opcional)",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="fs2_photos",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Atrás", key="fs2_back"):
                    st.session_state.form_step = 1
                    st.rerun()
            with c2:
                if st.button("Continuar →", type="primary", use_container_width=True, key="fs2_next"):
                    if not description.strip():
                        st.error("Describí qué necesitás resolver para continuar.")
                    else:
                        req["description"] = description.strip()
                        req["service_type"] = svc
                        req["category_label"] = category_label
                        st.session_state.form_step = 3
                        st.rerun()
        return

    if fs == 3:
        with st.container(border=True):
            st.markdown('<p class="form-step-num">Paso 3 · ¿Dónde?</p>', unsafe_allow_html=True)
            province = st.selectbox("Provincia", PROVINCES, index=PROVINCES.index(req.get("province", PROVINCES[1])) if req.get("province") in PROVINCES else 1)
            suggestions = locality_options(province)
            locality = st.selectbox("Localidad / ciudad", suggestions + ["Otra"]) if suggestions else "Otra"
            if locality == "Otra":
                locality = st.text_input("Ingresá tu localidad", value=req.get("locality", ""))
            neighborhood = st.text_input("Barrio (opcional)", value=req.get("neighborhood", ""))
            address = st.text_input("Calle y número", value=req.get("address", ""))
            apartment = st.text_input("Piso / departamento (opcional)", value=req.get("apartment", ""))
            reference = st.text_input("Referencia para llegar (opcional)", value=req.get("location_reference", ""))
            if address.strip():
                st.info(f"**Ubicación:** {location_summary(address, neighborhood, locality, province, apartment)}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Atrás", key="fs3_back"):
                    st.session_state.form_step = 2
                    st.rerun()
            with c2:
                if st.button("Continuar →", type="primary", use_container_width=True, key="fs3_next"):
                    if not address.strip() or not str(locality).strip():
                        st.error("Ingresá calle y localidad.")
                    else:
                        req.update({
                            "province": province, "locality": str(locality).strip(),
                            "neighborhood": neighborhood.strip(), "address": address.strip(),
                            "apartment": apartment.strip(), "location_reference": reference.strip(),
                            "location": location_summary(address, neighborhood, str(locality).strip(), province, apartment),
                        })
                        st.session_state.form_step = 4
                        st.rerun()
        return

    if fs == 4:
        with st.container(border=True):
            st.markdown('<p class="form-step-num">Paso 4 · ¿Cuándo?</p>', unsafe_allow_html=True)
            urgency = st.selectbox("Urgencia", URGENCY_LEVELS, index=URGENCY_LEVELS.index(req.get("urgency", "Programado")) if req.get("urgency") in URGENCY_LEVELS else 2)
            appt_date = st.date_input("Fecha", value=date.fromisoformat(req["preferred_date"]) if req.get("preferred_date") else min_appointment_date(urgency), min_value=min_appointment_date(urgency))
            slots = available_slots(urgency, appt_date)
            st.markdown("**Elegí un horario**")
            selected_slot = req.get("appointment_time") or req.get("preferred_time", "")
            if is_asap(selected_slot):
                selected_slot = ASAP
            for period, period_slots in grouped_slots(slots).items():
                if not period_slots:
                    continue
                st.markdown(f"*{period}*")
                cols = st.columns(3)
                for i, slot in enumerate(period_slots):
                    with cols[i % 3]:
                        slot_key = ASAP if is_asap(slot) else slot
                        slot_label = slot_display(slot)
                        btn_key = f"slot_{slot_key.replace(':', '')}"
                        if st.button(
                            slot_label,
                            key=btn_key,
                            type="primary" if selected_slot == slot_key else "secondary",
                            use_container_width=True,
                        ):
                            req["appointment_time"] = slot_key
                            req["preferred_time"] = slot_key
                            st.rerun()
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Atrás", key="fs4_back"):
                    st.session_state.form_step = 3
                    st.rerun()
            with c2:
                if st.button("Buscar profesionales", type="primary", use_container_width=True, key="fs4_next"):
                    if not req.get("appointment_time"):
                        st.error("Seleccioná un horario.")
                    else:
                        req["urgency"] = urgency
                        req["appointment_date"] = appt_date.isoformat()
                        req["preferred_date"] = appt_date.isoformat()
                        _go_to_professionals(req)
        return


def _profesionales() -> None:
    req = st.session_state.request
    if st.session_state.diagnosis:
        st.markdown(diagnosis_box_html(st.session_state.diagnosis), unsafe_allow_html=True)
    st.markdown(salvita_html("searching"), unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<p class="section-title">Profesionales verificados</p>', unsafe_allow_html=True)
        sort_by = st.selectbox("Ordenar por", ["Mejor calificados", "Menor precio", "Llega antes", "Más trabajos en tu zona", "Disponible hoy"], key="sort_filter")
        trade = st.session_state.diagnosis.get("recommended_trade", req["service_type"]) if st.session_state.diagnosis else req["service_type"]
        df = sort_professionals(
            recommend_professionals(
                trade, req["urgency"],
                req.get("appointment_time") or req.get("preferred_time", ""),
                neighborhood=req.get("neighborhood", ""),
                province=req.get("province", ""),
                locality=req.get("locality", ""),
            ),
            sort_by,
        )
        if df.empty:
            st.warning("No hay profesionales disponibles en tu zona.")
            if st.button("← Volver"):
                st.session_state.flow_step = 1
                st.rerun()
            return
        for _, pro in df.iterrows():
            pro_d = pro.to_dict()
            revs = get_reviews_for_professional(pro["id"], 2)
            rh = "".join(review_html(r["customer_name"], r["rating"], r["comment"], r.get("neighborhood", "")) for _, r in revs.iterrows())
            zone = req.get("locality") or "tu zona"
            st.markdown(pro_card_html(pro_d, zone, int(pro["neighborhood_jobs"]), pro["eta_label"], float(pro["estimated_price"]), rh), unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Ver perfil", key=f"vp_{pro['id']}"):
                    st.session_state.view_pro_id = pro["id"]
            with c2:
                if st.button("Elegir profesional", key=f"ep_{pro['id']}", type="primary", use_container_width=True):
                    st.session_state.selected_pro_id = pro["id"]
                    st.session_state.flow_step = 3
                    st.rerun()
            if st.session_state.get("view_pro_id") == pro["id"]:
                st.caption(BADGE_TOOLTIP)
                st.markdown(f"**Experiencia:** {pro.get('experience_years', 0)} años · **Cobertura:** {pro.get('city', '')}, {pro.get('province', '')}")
        if st.button("← Volver"):
            st.session_state.flow_step = 1
            st.rerun()


def _reserva() -> None:
    req = st.session_state.request
    pro = get_professional(st.session_state.selected_pro_id)
    if not pro:
        st.session_state.flow_step = 2
        st.rerun()
        return
    price = estimate_price(pro["base_price"], req["urgency"])
    eta = estimate_arrival(req["urgency"], int(pro.get("eta_base_minutes", 45)), True)
    appt = format_appointment(req.get("appointment_date", ""), req.get("appointment_time", ""))
    loc = req.get("location") or location_summary(req.get("address", ""), req.get("neighborhood", ""), req.get("locality", ""), req.get("province", ""), req.get("apartment", ""))

    bid = st.session_state.get("created_booking_id")
    if bid and st.session_state.get("show_booking_receipt"):
        booking = get_booking(bid)
        pro_d = get_professional(booking["professional_id"]) or pro
        amount = float(booking.get("approved_price") or booking.get("initial_price") or price)
        if booking.get("payment_status") == PAYMENT_CONFIRMED:
            st.markdown(booking_confirmed_receipt_html(booking, pro_d, amount, appt, loc), unsafe_allow_html=True)
            st.markdown(salvita_html("success", "Listo, tu reserva quedó confirmada."), unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Ir al seguimiento", type="primary", use_container_width=True):
                    st.session_state.show_booking_receipt = False
                    st.session_state.flow_step = 5
                    st.rerun()
            with c2:
                if st.button("Abrir chat", use_container_width=True):
                    st.session_state.show_chat = True
                    st.rerun()
            with c3:
                if st.button("Ver en Mis reservas", use_container_width=True):
                    go("Reservas")
        else:
            st.markdown(booking_pending_receipt_html(booking, pro_d, amount, appt, loc), unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Pagar y confirmar reserva", type="primary", use_container_width=True):
                    st.session_state.show_booking_receipt = False
                    st.session_state.flow_step = 4
                    st.rerun()
            with c2:
                if st.button("Volver a profesionales", use_container_width=True):
                    st.session_state.show_booking_receipt = False
                    st.session_state.flow_step = 2
                    st.rerun()
            with c3:
                if st.button("Ver en Mis reservas", use_container_width=True):
                    go("Reservas")
        if st.session_state.get("show_chat") and booking.get("payment_status") == PAYMENT_CONFIRMED:
            render_chat_panel(booking, pro_d)
        return

    with st.container(border=True):
        st.markdown('<p class="section-title">Confirmar reserva</p>', unsafe_allow_html=True)
        st.markdown(f"**Problema:** {req.get('description', '')}")
        st.markdown(f"**Profesional:** {pro['name']} · **Precio:** {format_ars(price)} ({pro.get('price_type', '')})")
        st.markdown(f"**Ubicación:** {loc}")
        st.markdown(f"**Turno:** {appt} · Llegada ~{eta}")
        st.info("El chat se habilitará cuando confirmes el pago.")
        st.caption(
            "Al confirmar la reserva, aceptás las "
            "[condiciones del servicio](#condiciones-servicio) y la "
            "[Garantía SALVA](#garantia-salva)."
        )
        with st.expander("Condiciones del servicio y Garantía SALVA", expanded=False):
            st.markdown(
                "**Condiciones del servicio:** el precio orientativo puede ajustarse "
                "tras la evaluación en domicilio. El turno queda reservado al confirmar."
            )
            st.markdown(
                "**Garantía SALVA:** cobertura post-servicio sujeta a revisión. "
                "Podés iniciar un reclamo formal desde Mi hogar o Garantía."
            )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Cambiar profesional"):
                st.session_state.flow_step = 2
                st.rerun()
        with c2:
            if st.button("Confirmar reserva", type="primary", use_container_width=True):
                b = create_booking(
                    customer_name=_customer_name(req), province=req.get("province", ""),
                    locality=req.get("locality", ""), neighborhood=req.get("neighborhood", ""),
                    address=req.get("address", ""), apartment=req.get("apartment", ""),
                    location_reference=req.get("location_reference", ""), location=loc,
                    service_type=req["service_type"], problem_description=req.get("description", ""),
                    urgency=req["urgency"], preferred_date=req.get("appointment_date", ""),
                    preferred_time=req.get("appointment_time", ""),
                    appointment_date=req.get("appointment_date", ""),
                    appointment_time=req.get("appointment_time", ""),
                    professional_id=pro["id"], estimated_arrival=str(eta), terms_accepted=True,
                )
                st.session_state.created_booking_id = b["id"]
                st.session_state.pending_payment_booking_id = b["id"]
                st.session_state.active_booking_id = b["id"]
                seed_booking_chat(b["id"], pro["name"], paid=False)
                add_system_message(b["id"], "Turno reservado")
                st.session_state.show_booking_receipt = True
                st.rerun()


def _pago() -> None:
    bid = st.session_state.pending_payment_booking_id or st.session_state.created_booking_id
    booking = get_booking(bid) if bid else None
    if not booking:
        st.session_state.flow_step = 3
        st.rerun()
        return
    if booking.get("payment_status") == PAYMENT_CONFIRMED:
        if st.session_state.get("show_payment_receipt"):
            amount = float(booking.get("approved_price") or booking.get("initial_price") or 0)
            pro_d = get_professional(booking["professional_id"]) or {}
            appt = appointment_label(booking)
            loc = booking.get("location", "")
            st.markdown(booking_confirmed_receipt_html(booking, pro_d, amount, appt, loc), unsafe_allow_html=True)
            if st.button("Ir al seguimiento", type="primary", use_container_width=True):
                st.session_state.show_payment_receipt = False
                st.session_state.flow_step = 5
                st.rerun()
            return
        st.session_state.flow_step = 5
        st.rerun()
        return
    pro = get_professional(booking["professional_id"])
    amount = float(booking.get("approved_price") or booking.get("initial_price") or 0)
    with st.container(border=True):
        st.markdown('<p class="section-title">Completar pago</p>', unsafe_allow_html=True)
        st.markdown(f"**{booking['professional_name']}** · {booking['service_type']} · **{format_ars(amount)}** · {booking['id']}")
        method = st.radio("Método de pago", PAYMENT_METHODS)
        if method == "Tarjeta de crédito":
            st.markdown('<div class="sim-banner">Pago simulado para fines académicos. SALVA no almacena datos sensibles de la tarjeta.</div>', unsafe_allow_html=True)
            with st.form(f"pay_card_{bid}"):
                cn_raw = st.text_input(
                    "Número de tarjeta",
                    placeholder="1234 5678 9012 3456",
                    max_chars=19,
                    help="Ingresá los 16 números de la tarjeta",
                )
                cn = sanitize_card_input(cn_raw)
                brand = detect_card_brand(cn)
                st.markdown(card_brands_html(brand), unsafe_allow_html=True)
                st.caption("Ingresá los 16 números de la tarjeta.")
                holder = st.text_input("Titular de la tarjeta")
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    month = st.text_input("Mes (MM)", placeholder="MM", max_chars=2)
                with c2:
                    year = st.text_input("Año (AA)", placeholder="AA", max_chars=2)
                with c3:
                    cvv = st.text_input("CVV", type="password", max_chars=3)
                st.caption("Formato visual: MM / AA")
                if st.form_submit_button("Confirmar pago simulado", type="primary", use_container_width=True):
                    ok, msg, brand = validate_card(
                        cn_raw, holder, sanitize_month(month), sanitize_year(year), sanitize_cvv(cvv)
                    )
                    if ok:
                        digits = "".join(ch for ch in cn_raw if ch.isdigit())
                        confirm_payment(bid, method, digits[-4:], brand)
                        add_system_message(bid, "Pago confirmado")
                        st.session_state.show_payment_receipt = True
                        st.rerun()
                    else:
                        st.error(msg)
        elif method == "SALVA Cuenta":
            from services.accounts import get_balance, pay_from_cuenta, ACCOUNT_CUENTA
            bal = get_balance(ACCOUNT_CUENTA)
            st.markdown(f"**Saldo SALVA Cuenta:** {format_ars(bal)}")
            if st.button("Pagar con SALVA Cuenta", type="primary", use_container_width=True):
                ok, msg = pay_from_cuenta(amount, bid, f"Pago servicio {booking['service_type']}")
                if ok:
                    confirm_payment(bid, method, "", "")
                    add_system_message(bid, "Pago confirmado")
                    st.session_state.show_payment_receipt = True
                    st.rerun()
                else:
                    st.error(msg)
        else:
            alias = pro.get("bank_alias", "salva.pago") if pro else "salva.pago"
            st.markdown(f"**Alias:** `{alias}` · **Monto:** {format_ars(amount)} · Ref: {booking['id']}")
            if st.button("Confirmar pago simulado", type="primary", use_container_width=True):
                confirm_payment(bid, method)
                add_system_message(bid, "Pago confirmado")
                st.session_state.show_payment_receipt = True
                st.rerun()


def _seguimiento() -> None:
    bid = st.session_state.active_booking_id or st.session_state.created_booking_id
    booking = get_booking(bid) if bid else None
    if not booking or booking.get("payment_status") != PAYMENT_CONFIRMED:
        st.session_state.flow_step = 4
        st.rerun()
        return
    pro = get_professional(booking["professional_id"]) or {}
    current = booking.get("service_status") or SERVICE_STATUS_FLOW[0]
    with st.container(border=True):
        st.markdown('<p class="section-title">Seguimiento</p>', unsafe_allow_html=True)
        st.markdown(salvita_html("travelling", "Tu profesional está en camino."), unsafe_allow_html=True)
        if pro:
            c1, c2 = st.columns([1, 3])
            with c1:
                from services.ui_components import avatar_img_html
                st.markdown(avatar_img_html(pro, 72), unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{booking['professional_name']}**")
                st.caption(f"Llegada estimada: {booking.get('estimated_arrival', '—')}")
        st.markdown(tracking_road_html(current, SERVICE_STATUS_FLOW, booking.get("service_type", ""), pro), unsafe_allow_html=True)
        st.caption("Control de demostración")
        bc1, bc2 = st.columns(2)
        with bc1:
            if current != "Servicio finalizado" and not booking.get("price_change_proposed"):
                if st.button("Continuar al siguiente estado", type="primary", use_container_width=True, key="adv_track"):
                    advance_service_status(booking["id"])
                    st.rerun()
        with bc2:
            if st.button("Ver chat", use_container_width=True, key="track_chat"):
                st.session_state.show_chat = True
                st.rerun()
        st.markdown(f"**Turno:** {appointment_label(booking)}")
        st.markdown(f"**Ubicación:** {booking.get('location', '—')}")
        st.markdown(f"**Monto:** {format_ars(booking.get('approved_price') or booking.get('initial_price'))}")
        if st.session_state.get("show_chat"):
            render_chat_panel(booking, pro)
        if booking.get("price_change_proposed"):
            st.warning(f"Cambio propuesto: {format_ars(booking['price_change_proposed'])} — {booking.get('price_change_reason', '')}")
            if st.button("Aceptar nuevo precio", type="primary"):
                accept_price_change(booking["id"])
                st.rerun()
            if st.button("Rechazar y solicitar asistencia"):
                go("Garantía")
        else:
            if st.button("Simular cambio de precio", use_container_width=True):
                p = float(booking.get("approved_price") or booking.get("initial_price")) * 1.1
                propose_price_change(booking["id"], p, "Materiales adicionales en sitio.")
                st.rerun()
    if current == "Servicio finalizado":
        st.session_state.flow_step = 6
        st.rerun()


def _finalizacion() -> None:
    bid = st.session_state.active_booking_id or st.session_state.created_booking_id
    booking = get_booking(bid) if bid else None
    if not booking:
        return
    pro = get_professional(booking["professional_id"]) or {}
    existing = get_rating(booking["id"])
    work_done = (
        booking.get("work_completed")
        or booking.get("problem_description")
        or booking.get("service_type")
        or "Servicio completado"
    )
    with st.container(border=True):
        st.markdown('<p class="section-title">Servicio finalizado</p>', unsafe_allow_html=True)
        st.markdown(
            f"**{booking['service_type']}** con {booking['professional_name']} · "
            f"{format_ars(booking.get('approved_price') or booking.get('initial_price'))}"
        )
        if existing and existing.get("rating"):
            st.markdown(
                completed_service_receipt_html(
                    booking,
                    pro,
                    int(existing["rating"]),
                    existing.get("comment", ""),
                    work_done,
                ),
                unsafe_allow_html=True,
            )
            _completion_actions()
            return
        st.markdown("#### Calificá tu experiencia")
        rating = render_star_rating(booking["id"])
        st.info("Sumás puntos SALVA si compartís una reseña y ayudás a otros usuarios a elegir mejor.")
        with st.form(f"fin_{booking['id']}"):
            review = st.text_area(
                "Reseña",
                height=100,
                placeholder="Contanos cómo fue tu experiencia (opcional)",
            )
            submitted = st.form_submit_button(
                "Enviar calificación",
                type="primary",
                disabled=not bool(rating),
            )
        if st.button("Reportar un problema", key=f"fin_issue_pre_{booking['id']}", use_container_width=True):
            go("Garantía")
        if submitted:
            rating = st.session_state.get(f"rating_val_{booking['id']}")
            if not rating:
                st.error("Seleccioná una calificación con estrellas.")
            elif st.session_state.get(f"review_saved_{booking['id']}"):
                st.warning("Esta calificación ya fue enviada.")
            else:
                comment = review.strip() if review.strip() else "Sin comentario adicional."
                submit_completion(booking, int(rating), comment, work_done, "")
                update_booking(booking["id"], work_completed=work_done)
                st.session_state[f"review_saved_{booking['id']}"] = True
                st.session_state[f"rating_done_{booking['id']}"] = True
                st.balloons()
                st.rerun()


def _completion_actions() -> None:
    st.markdown("#### ¿Qué querés hacer ahora?")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Volver al inicio", type="primary", use_container_width=True, key="fin_home"):
            clear_active_flow()
            go("Inicio")
    with c2:
        if st.button("Ver en SALVA Historial", use_container_width=True, key="fin_hist"):
            go("Mi hogar")
    with c3:
        if st.button("Reportar un problema", use_container_width=True, key="fin_issue"):
            go("Garantía")
