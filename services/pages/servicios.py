"""Flujo de solicitud de servicio — 6 pasos."""

import time
from datetime import date

import streamlit as st

from services.auth import authenticated_user
from services.bookings import (
    SERVICE_STATUS_FLOW,
    accept_price_change,
    advance_service_status,
    appointment_label,
    can_access_tracking,
    can_pay_remaining,
    create_booking,
    get_booking,
    is_deposit_confirmed,
    is_fully_paid,
    normalize_service_status,
    propose_price_change,
    update_booking,
)
from services.chat import add_system_message, seed_booking_chat
from services.diagnosis import build_diagnosis
from services.formatting import format_ars
from services.locations import PROVINCES, locality_options, location_summary
from services.navigation import clear_active_flow, go
from services.pricing import booking_totals, prices_from_professionals, split_deposit
from services.service_categories import category_internal, category_label as visible_category_label, resolve_selection
from services.service_guides import guide_for_category, render_category_guide
from services.ui_components import (
    booking_confirmed_receipt_html,
    card_brands_html,
    completed_service_receipt_html,
    diagnosis_box_html,
    form_category_picker,
    pro_card_html,
    remaining_payment_receipt_html,
    render_chat_panel,
    render_flow_indicator,
    render_star_rating,
    reservation_summary_card_html,
    review_html,
    tracking_road_html,
)
from services.payments import (
    PAYMENT_METHODS,
    confirm_deposit,
    confirm_remaining,
    detect_card_brand,
    sanitize_card_input,
    sanitize_cvv,
    sanitize_month,
    sanitize_year,
    validate_card,
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
    ASAP,
    URGENCY_LEVELS,
    available_slots,
    format_appointment,
    format_selected_turno,
    is_asap,
    min_appointment_date,
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
            address = st.text_input("Calle y número", value=req.get("address", ""))
            apartment = st.text_input("Piso / departamento (opcional)", value=req.get("apartment", ""))
            neighborhood = st.text_input("Barrio (opcional)", value=req.get("neighborhood", ""))
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
            urgency = st.selectbox(
                "Urgencia",
                URGENCY_LEVELS,
                index=URGENCY_LEVELS.index(req.get("urgency", "Programado")) if req.get("urgency") in URGENCY_LEVELS else 2,
            )
            appt_date = st.date_input(
                "Fecha",
                value=date.fromisoformat(req["preferred_date"]) if req.get("preferred_date") else min_appointment_date(urgency),
                min_value=min_appointment_date(urgency),
            )

            if urgency == "Emergencia":
                # Valor interno seguro (string); nunca se parsea como entero.
                req["appointment_time"] = ASAP
                req["preferred_time"] = ASAP
                st.info("Buscaremos al profesional disponible más cercano")
            else:
                # Solo franjas HH:MM; excluye ASAP / "Lo antes posible" del selector.
                slots = [
                    s for s in available_slots(urgency, appt_date)
                    if not is_asap(s) and ":" in str(s)
                ]
                st.markdown("**Elegí un horario**")
                current = str(req.get("appointment_time") or req.get("preferred_time") or "")
                if is_asap(current) or current not in slots:
                    current = ""
                widget_key = f"fs4_time_{urgency}_{appt_date.isoformat()}"
                if st.session_state.get(widget_key) not in slots:
                    st.session_state[widget_key] = current or None
                choice = st.selectbox(
                    "Horario",
                    options=slots,
                    placeholder="Seleccioná un horario",
                    label_visibility="collapsed",
                    key=widget_key,
                )
                if choice:
                    req["appointment_time"] = choice
                    req["preferred_time"] = choice
                    confirm = format_selected_turno(appt_date, choice)
                    if confirm:
                        st.success(confirm)
                else:
                    req["appointment_time"] = ""
                    req["preferred_time"] = ""

            has_time = bool(str(req.get("appointment_time") or "").strip())
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Atrás", key="fs4_back"):
                    st.session_state.form_step = 3
                    st.rerun()
            with c2:
                if st.button(
                    "Buscar profesionales",
                    type="primary",
                    use_container_width=True,
                    key="fs4_next",
                    disabled=not has_time,
                ):
                    if not has_time:
                        st.error("Seleccioná un horario.")
                    else:
                        req["urgency"] = urgency
                        req["appointment_date"] = appt_date.isoformat()
                        req["preferred_date"] = appt_date.isoformat()
                        _go_to_professionals(req)
        return


def _profesionales() -> None:
    req = st.session_state.request
    with st.container(border=True):
        st.markdown('<p class="section-title">Profesionales verificados</p>', unsafe_allow_html=True)
        sort_by = st.selectbox(
            "Ordenar por",
            ["Mejor calificados", "Menor precio", "Llega antes", "Más trabajos en tu zona", "Disponible hoy"],
            key="sort_filter",
        )
        trade = (
            st.session_state.diagnosis.get("recommended_trade", req["service_type"])
            if st.session_state.diagnosis
            else req["service_type"]
        )
        df = sort_professionals(
            recommend_professionals(
                trade,
                req["urgency"],
                req.get("appointment_time") or req.get("preferred_time", ""),
                neighborhood=req.get("neighborhood", ""),
                province=req.get("province", ""),
                locality=req.get("locality", ""),
            ),
            sort_by,
        )
        # Rango alineado exclusivamente a los profesionales visibles
        if st.session_state.diagnosis is not None:
            if df.empty:
                st.session_state.diagnosis["price_range_low"] = None
                st.session_state.diagnosis["price_range_high"] = None
                st.session_state.diagnosis["professionals_available"] = 0
            else:
                low, high = prices_from_professionals(df["estimated_price"].tolist())
                st.session_state.diagnosis["price_range_low"] = low
                st.session_state.diagnosis["price_range_high"] = high
                st.session_state.diagnosis["professionals_available"] = len(df)
        if st.session_state.diagnosis:
            st.markdown(diagnosis_box_html(st.session_state.diagnosis), unsafe_allow_html=True)
        st.markdown(salvita_html("searching"), unsafe_allow_html=True)
        if df.empty:
            st.warning("No hay profesionales disponibles en tu zona.")
            if st.button("← Volver"):
                st.session_state.flow_step = 1
                st.rerun()
            return
        for _, pro in df.iterrows():
            pro_d = pro.to_dict()
            revs = get_reviews_for_professional(pro["id"], 2)
            rh = "".join(
                review_html(r["customer_name"], r["rating"], r["comment"], r.get("neighborhood", ""))
                for _, r in revs.iterrows()
            )
            zone = req.get("locality") or "tu zona"
            st.markdown(
                pro_card_html(pro_d, zone, int(pro["neighborhood_jobs"]), pro["eta_label"], float(pro["estimated_price"]), rh),
                unsafe_allow_html=True,
            )
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
                st.markdown(
                    f"**Experiencia:** {pro.get('experience_years', 0)} años · "
                    f"**Cobertura:** {pro.get('city', '')}, {pro.get('province', '')}"
                )
        if st.button("← Volver"):
            st.session_state.flow_step = 1
            st.rerun()


def _render_money_methods(booking: dict, amount: float, kind: str, form_key: str) -> bool:
    """Formulario de pago simulado. kind: deposit|remaining. Devuelve True si cobró."""
    pro = get_professional(booking["professional_id"])
    method = st.radio("Método de pago", PAYMENT_METHODS, key=f"{form_key}_method")
    paid = False
    if method == "Tarjeta de crédito":
        st.markdown(
            '<div class="sim-banner">Pago simulado para fines académicos. '
            "SALVA no almacena datos sensibles de la tarjeta.</div>",
            unsafe_allow_html=True,
        )
        with st.form(f"{form_key}_card"):
            cn_raw = st.text_input(
                "Número de tarjeta",
                placeholder="1234 5678 9012 3456",
                max_chars=19,
                help="Ingresá los 16 números de la tarjeta",
            )
            cn = sanitize_card_input(cn_raw)
            brand = detect_card_brand(cn)
            st.markdown(card_brands_html(brand), unsafe_allow_html=True)
            holder = st.text_input("Titular de la tarjeta")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                month = st.text_input("Mes (MM)", placeholder="MM", max_chars=2)
            with c2:
                year = st.text_input("Año (AA)", placeholder="AA", max_chars=2)
            with c3:
                cvv = st.text_input("CVV", type="password", max_chars=3)
            label = f"Pagar seña de {format_ars(amount)}" if kind == "deposit" else f"Pagar saldo de {format_ars(amount)}"
            if st.form_submit_button(label, type="primary", use_container_width=True):
                ok, msg, brand = validate_card(
                    cn_raw, holder, sanitize_month(month), sanitize_year(year), sanitize_cvv(cvv)
                )
                if ok:
                    digits = "".join(ch for ch in cn_raw if ch.isdigit())
                    if kind == "deposit":
                        confirm_deposit(booking["id"], method, digits[-4:], brand)
                        add_system_message(booking["id"], "Seña confirmada")
                    else:
                        confirm_remaining(booking["id"], method, digits[-4:], brand)
                        add_system_message(booking["id"], "Pago completado")
                    paid = True
                else:
                    st.error(msg)
    elif method == "SALVA Cuenta":
        from services.accounts import ACCOUNT_CUENTA, get_balance, pay_from_cuenta

        bal = get_balance(ACCOUNT_CUENTA)
        st.markdown(f"**Saldo SALVA Cuenta:** {format_ars(bal)}")
        btn = f"Pagar seña con SALVA Cuenta ({format_ars(amount)})" if kind == "deposit" else f"Pagar saldo con SALVA Cuenta ({format_ars(amount)})"
        if st.button(btn, type="primary", use_container_width=True, key=f"{form_key}_cuenta"):
            desc = f"Seña {booking['service_type']}" if kind == "deposit" else f"Saldo {booking['service_type']}"
            ok, msg = pay_from_cuenta(float(amount), booking["id"], desc)
            if ok:
                if kind == "deposit":
                    confirm_deposit(booking["id"], method, "", "")
                    add_system_message(booking["id"], "Seña confirmada")
                else:
                    confirm_remaining(booking["id"], method, "", "")
                    add_system_message(booking["id"], "Pago completado")
                paid = True
            else:
                st.error(msg)
    else:
        alias = pro.get("bank_alias", "salva.pago") if pro else "salva.pago"
        st.markdown(f"**Alias:** `{alias}` · **Monto:** {format_ars(amount)} · Ref: {booking['id']}")
        btn = f"Confirmar seña simulada ({format_ars(amount)})" if kind == "deposit" else f"Confirmar saldo simulado ({format_ars(amount)})"
        if st.button(btn, type="primary", use_container_width=True, key=f"{form_key}_xfer"):
            if kind == "deposit":
                confirm_deposit(booking["id"], method)
                add_system_message(booking["id"], "Seña confirmada")
            else:
                confirm_remaining(booking["id"], method)
                add_system_message(booking["id"], "Pago completado")
            paid = True
    return paid


def _reserva() -> None:
    req = st.session_state.request
    pro = get_professional(st.session_state.selected_pro_id)
    if not pro:
        st.session_state.flow_step = 2
        st.rerun()
        return
    price = float(estimate_price(pro["base_price"], req["urgency"]))
    total, deposit, remaining = split_deposit(price)
    eta = estimate_arrival(req["urgency"], int(pro.get("eta_base_minutes", 45)), True)
    appt = format_appointment(req.get("appointment_date", ""), req.get("appointment_time", ""))
    loc = req.get("location") or location_summary(
        req.get("address", ""),
        req.get("neighborhood", ""),
        req.get("locality", ""),
        req.get("province", ""),
        req.get("apartment", ""),
    )
    price_type = str(pro.get("price_type", "Precio orientativo"))

    bid = st.session_state.get("created_booking_id")
    booking = get_booking(bid) if bid else None

    # Comprobante post-seña
    if booking and is_deposit_confirmed(booking) and st.session_state.get("show_booking_receipt"):
        pro_d = get_professional(booking["professional_id"]) or pro
        st.markdown(
            booking_confirmed_receipt_html(booking, pro_d, float(total), appointment_label(booking), booking.get("location", loc)),
            unsafe_allow_html=True,
        )
        st.markdown(salvita_html("success", "Listo, tu seña quedó confirmada."), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Ir al seguimiento", type="primary", use_container_width=True):
                st.session_state.show_booking_receipt = False
                st.session_state.show_deposit_payment = False
                st.session_state.flow_step = 5
                st.rerun()
        with c2:
            if st.button("Abrir chat", use_container_width=True):
                st.session_state.show_chat = True
                st.rerun()
        with c3:
            if st.button("Ver en Mi hogar", use_container_width=True):
                go("Mi hogar")
        if st.session_state.get("show_chat"):
            render_chat_panel(booking, pro_d)
        return

    # Formulario de pago de seña (misma etapa Reserva)
    if booking and not is_deposit_confirmed(booking) and st.session_state.get("show_deposit_payment"):
        totals = booking_totals(booking)
        with st.container(border=True):
            st.markdown('<p class="section-title">Pagar seña para confirmar</p>', unsafe_allow_html=True)
            st.markdown(
                reservation_summary_card_html(
                    pro,
                    booking.get("service_type", ""),
                    appointment_label(booking),
                    booking.get("location", loc),
                    float(totals["total"]),
                    float(totals["deposit"]),
                    float(totals["remaining"]),
                    booking.get("price_type", price_type),
                ),
                unsafe_allow_html=True,
            )
            st.info(
                "La reserva quedará confirmada cuando se acredite la seña. "
                "El importe se descontará del total del servicio."
            )
            st.caption(
                "La devolución o retención de la seña dependerá de las condiciones de cancelación "
                "de la reserva. Operación simulada para fines académicos."
            )
            if _render_money_methods(booking, float(totals["deposit"]), "deposit", f"dep_{booking['id']}"):
                st.session_state.show_booking_receipt = True
                st.session_state.show_deposit_payment = False
                st.rerun()
        return

    # Confirmación previa (crear reserva)
    with st.container(border=True):
        st.markdown('<p class="section-title">Confirmar reserva</p>', unsafe_allow_html=True)
        st.markdown(
            reservation_summary_card_html(
                pro,
                req.get("service_type", ""),
                appt,
                loc,
                float(total),
                float(deposit),
                float(remaining),
                price_type,
            ),
            unsafe_allow_html=True,
        )
        st.markdown(f"**Problema:** {req.get('description', '')}")
        st.markdown(f"**Llegada estimada:** ~{eta}")
        if "orientativo" in price_type.lower():
            st.info(
                "El valor se toma como base para calcular la seña. Si el alcance o el precio cambia, "
                "deberá informarse y ser aprobado por el cliente dentro de SALVA antes de continuar."
            )
        st.info(
            "La reserva quedará confirmada cuando se acredite la seña. "
            "El importe se descontará del total del servicio."
        )
        st.caption(
            "Al confirmar la reserva, aceptás las "
            "[condiciones del servicio](#condiciones-servicio) y la "
            "[Garantía SALVA](#garantia-salva)."
        )
        st.caption(
            "La devolución o retención de la seña dependerá de las condiciones de cancelación "
            "de la reserva. Operación simulada para fines académicos."
        )
        with st.expander("Condiciones del servicio y Garantía SALVA", expanded=False):
            st.markdown(
                "**Condiciones del servicio:** el precio orientativo puede ajustarse "
                "tras la evaluación en domicilio. El turno queda reservado al confirmar la seña."
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
            if st.button(
                f"Confirmar y pagar seña de {format_ars(deposit)}",
                type="primary",
                use_container_width=True,
            ):
                b = create_booking(
                    customer_name=_customer_name(req),
                    province=req.get("province", ""),
                    locality=req.get("locality", ""),
                    neighborhood=req.get("neighborhood", ""),
                    address=req.get("address", ""),
                    apartment=req.get("apartment", ""),
                    location_reference=req.get("location_reference", ""),
                    location=loc,
                    service_type=req["service_type"],
                    problem_description=req.get("description", ""),
                    urgency=req["urgency"],
                    preferred_date=req.get("appointment_date", ""),
                    preferred_time=req.get("appointment_time", ""),
                    appointment_date=req.get("appointment_date", ""),
                    appointment_time=req.get("appointment_time", ""),
                    professional_id=pro["id"],
                    estimated_arrival=str(eta),
                    terms_accepted=True,
                )
                st.session_state.created_booking_id = b["id"]
                st.session_state.pending_payment_booking_id = b["id"]
                st.session_state.active_booking_id = b["id"]
                seed_booking_chat(b["id"], pro["name"], paid=False)
                add_system_message(b["id"], "Turno reservado")
                st.session_state.show_deposit_payment = True
                st.session_state.show_booking_receipt = False
                st.rerun()


def _pago() -> None:
    """Paso Pago: redirige a seña (Reserva) o cobra el saldo pendiente."""
    bid = st.session_state.pending_payment_booking_id or st.session_state.created_booking_id or st.session_state.active_booking_id
    booking = get_booking(bid) if bid else None
    if not booking:
        st.session_state.flow_step = 3
        st.rerun()
        return

    if not is_deposit_confirmed(booking):
        st.session_state.created_booking_id = booking["id"]
        st.session_state.show_deposit_payment = True
        st.session_state.flow_step = 3
        st.rerun()
        return

    if is_fully_paid(booking):
        if st.session_state.get("show_payment_receipt"):
            pro_d = get_professional(booking["professional_id"]) or {}
            st.markdown(
                remaining_payment_receipt_html(
                    booking, pro_d, appointment_label(booking), booking.get("location", "")
                ),
                unsafe_allow_html=True,
            )
            if st.button("Continuar a calificación", type="primary", use_container_width=True):
                st.session_state.show_payment_receipt = False
                st.session_state.flow_step = 6
                st.rerun()
            return
        st.session_state.flow_step = 6
        st.rerun()
        return

    if not can_pay_remaining(booking):
        st.info("El saldo del 80% se habilita cuando el trabajo esté finalizado.")
        if st.button("Ir al seguimiento", type="primary", use_container_width=True):
            st.session_state.flow_step = 5
            st.rerun()
        return

    totals = booking_totals(booking)
    with st.container(border=True):
        st.markdown('<p class="section-title">El trabajo fue finalizado</p>', unsafe_allow_html=True)
        st.markdown(f"**Precio total:** {format_ars(totals['total'])}")
        st.markdown(f"**Seña abonada:** {format_ars(totals['deposit'])}")
        st.markdown(f"**Saldo a pagar (80%):** {format_ars(totals['remaining'])}")
        if _render_money_methods(booking, float(totals["remaining"]), "remaining", f"rem_{booking['id']}"):
            st.session_state.show_payment_receipt = True
            st.rerun()


def _seguimiento() -> None:
    bid = st.session_state.active_booking_id or st.session_state.created_booking_id
    booking = get_booking(bid) if bid else None
    if not booking or not can_access_tracking(booking):
        st.session_state.flow_step = 3
        st.session_state.show_deposit_payment = True
        st.rerun()
        return

    if is_fully_paid(booking) and normalize_service_status(booking) == "Pago completado":
        st.session_state.flow_step = 6
        st.rerun()
        return

    pro = get_professional(booking["professional_id"]) or {}
    current = normalize_service_status(booking)
    totals = booking_totals(booking)

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
        st.markdown(
            tracking_road_html(current, SERVICE_STATUS_FLOW, booking.get("service_type", ""), pro),
            unsafe_allow_html=True,
        )
        st.markdown(f"**Precio total:** {format_ars(totals['total'])}")
        st.markdown(f"**Seña abonada:** {format_ars(totals['deposit'])}")
        st.markdown(f"**Saldo pendiente:** {format_ars(totals['remaining'])}")
        st.markdown(f"**Turno:** {appointment_label(booking)}")
        st.markdown(f"**Ubicación:** {booking.get('location', '—')}")

        # Pago del saldo cuando el trabajo terminó
        if can_pay_remaining(booking) or current in ("Servicio finalizado", "Saldo pendiente"):
            if current == "Servicio finalizado":
                # Pasar a Saldo pendiente para desbloquear UI de cobro
                if str(booking.get("remaining_status") or "") != "pendiente":
                    advance_service_status(booking["id"])
                    st.rerun()
                    return
            st.markdown("---")
            st.markdown("### El trabajo fue finalizado")
            st.markdown(f"**Precio total:** {format_ars(totals['total'])}")
            st.markdown(f"**Seña abonada:** {format_ars(totals['deposit'])}")
            st.markdown(f"**Saldo a pagar (80%):** {format_ars(totals['remaining'])}")
            if st.button(
                f"Pagar saldo de {format_ars(totals['remaining'])}",
                type="primary",
                use_container_width=True,
                key="track_pay_remaining",
            ):
                st.session_state.flow_step = 4
                st.rerun()
        else:
            st.caption("Control de demostración")
            bc1, bc2 = st.columns(2)
            with bc1:
                if current not in ("Saldo pendiente", "Pago completado") and not booking.get("price_change_proposed"):
                    if st.button("Continuar al siguiente estado", type="primary", use_container_width=True, key="adv_track"):
                        advance_service_status(booking["id"])
                        st.rerun()
            with bc2:
                if st.button("Ver chat", use_container_width=True, key="track_chat"):
                    st.session_state.show_chat = True
                    st.rerun()

        if st.session_state.get("show_chat"):
            render_chat_panel(booking, pro)

        if booking.get("price_change_proposed"):
            st.warning(
                f"Cambio propuesto: {format_ars(booking['price_change_proposed'])} — "
                f"{booking.get('price_change_reason', '')}"
            )
            st.caption("La seña ya abonada no se recalcula; solo se actualiza el saldo pendiente.")
            if st.button("Aceptar nuevo precio", type="primary"):
                accept_price_change(booking["id"])
                st.rerun()
            if st.button("Rechazar y solicitar asistencia"):
                go("Garantía")
        elif current not in ("Saldo pendiente", "Pago completado", "Servicio finalizado"):
            if st.button("Simular cambio de precio", use_container_width=True):
                p = float(totals["total"]) * 1.1
                propose_price_change(booking["id"], p, "Materiales adicionales en sitio.")
                st.rerun()


def _finalizacion() -> None:
    bid = st.session_state.active_booking_id or st.session_state.created_booking_id
    booking = get_booking(bid) if bid else None
    if not booking:
        return
    if not is_fully_paid(booking):
        if can_pay_remaining(booking):
            st.session_state.flow_step = 4
        elif can_access_tracking(booking):
            st.session_state.flow_step = 5
        else:
            st.session_state.flow_step = 3
            st.session_state.show_deposit_payment = True
        st.rerun()
        return

    pro = get_professional(booking["professional_id"]) or {}
    existing = get_rating(booking["id"])
    work_done = (
        booking.get("work_completed")
        or booking.get("problem_description")
        or booking.get("service_type")
        or "Servicio completado"
    )
    totals = booking_totals(booking)
    with st.container(border=True):
        st.markdown('<p class="section-title">Servicio finalizado</p>', unsafe_allow_html=True)
        st.markdown(
            f"**{booking['service_type']}** con {booking['professional_name']} · "
            f"Total {format_ars(totals['total'])} · Seña {format_ars(totals['deposit'])} · "
            f"Saldo {format_ars(totals['remaining'])}"
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
        if st.button("Reportar un problema / iniciar reclamo", key=f"fin_issue_pre_{booking['id']}", use_container_width=True):
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
