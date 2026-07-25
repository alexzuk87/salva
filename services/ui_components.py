"""Componentes visuales reutilizables SALVA."""

import base64
import html
from pathlib import Path

import streamlit as st

from services.branding import read_svg, SYMBOL_WHITE
from services.formatting import format_ars
from services.icons import BENEFITS, ICONS
from services.pro_photos import avatar_img_html
from services.service_characters import (
    HOME_CATEGORIES,
    SERVICE_ICON_KEY,
    CATEGORY_ACCENTS,
    character_img_html,
    character_image_path,
)
from services.professionals import BADGE_TOOLTIP

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_CATEGORY_FLOAT_DELAYS = {
    "plomeria": 0.0,
    "electricidad": 0.35,
    "gas": 0.7,
    "cerrajeria": 1.05,
    "limpieza": 0.2,
    "pintura": 0.55,
    "electrodomesticos": 0.9,
    "jardineria": 1.25,
    "albanileria": 0.45,
    "aire": 0.8,
    "carpinteria": 1.15,
    "todos": 0.15,
}


def _svg_data_uri(path: Path) -> str:
    """Data URI base64 — compatible con Streamlit Community Cloud en CSS."""
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _service_category_css(categories) -> str:
    """CSS dinámico: botón compacto con ícono inline (base64) + nombre."""
    rules = [
        "@keyframes svcIconFloat {",
        "  0%, 100% { transform: translateY(0); }",
        "  50% { transform: translateY(-3px); }",
        "}",
        "@media (prefers-reduced-motion: reduce) {",
        "  div[data-testid='stVerticalBlock']:has(.svc-cat-grid-root) .stButton > button::before {",
        "    animation: none !important; transform: none !important;",
        "  }",
        "}",
        "@media (max-width: 480px) {",
        "  div[data-testid='stVerticalBlock']:has(.svc-cat-grid-root) .stButton > button::before {",
        "    width: 26px !important; height: 26px !important;",
        "  }",
        "  div[data-testid='stVerticalBlock']:has(.svc-cat-grid-root) .stButton > button {",
        "    min-height: 54px !important; font-size: 0.74rem !important; gap: 8px !important;",
        "  }",
        "}",
    ]
    for _label, char_key, _mapped, _desc in categories:
        path = character_image_path(char_key)
        if not path or not path.is_file():
            continue
        uri = _svg_data_uri(path)
        accent = CATEGORY_ACCENTS.get(char_key, "#365CF5")
        delay = _CATEGORY_FLOAT_DELAYS.get(char_key, 0.0)
        sel = (
            f"div[data-testid='column']:has(.svc-cat-{char_key}) .stButton > button, "
            f"div[data-testid='stVerticalBlock']:has(.svc-cat-{char_key}) .stButton > button"
        )
        rules.extend([
            f"{sel} {{",
            f"  display: inline-flex !important;",
            f"  flex-direction: row !important;",
            f"  align-items: center !important;",
            f"  justify-content: center !important;",
            f"  gap: 9px !important;",
            f"  background: var(--salva-surface) !important;",
            f"  border: 1px solid var(--salva-border) !important;",
            f"  border-radius: 16px !important;",
            f"  box-shadow: none !important;",
            f"  color: var(--salva-text) !important;",
            f"  -webkit-text-fill-color: var(--salva-text) !important;",
            f"  min-height: 58px !important;",
            f"  padding: 10px 12px !important;",
            f"  font-weight: 700 !important;",
            f"  font-size: 0.8rem !important;",
            f"  line-height: 1.15 !important;",
            f"  white-space: nowrap !important;",
            f"  overflow: hidden !important;",
            f"  text-overflow: ellipsis !important;",
            f"  transition: border-color 0.2s, background 0.2s !important;",
            f"}}",
            f"div[data-testid='column']:has(.svc-cat-{char_key}) .stButton > button::before,",
            f"div[data-testid='stVerticalBlock']:has(.svc-cat-{char_key}) .stButton > button::before {{",
            f'  content: "" !important;',
            f"  display: inline-block !important;",
            f"  flex-shrink: 0 !important;",
            f"  width: 30px !important;",
            f"  height: 30px !important;",
            f"  background-image: url('{uri}') !important;",
            f"  background-repeat: no-repeat !important;",
            f"  background-position: center !important;",
            f"  background-size: contain !important;",
            f"  animation: svcIconFloat 3.2s ease-in-out infinite alternate !important;",
            f"  animation-delay: {delay}s !important;",
            f"  will-change: transform !important;",
            f"}}",
            f"div[data-testid='column']:has(.svc-cat-{char_key}) .stButton > button:hover,",
            f"div[data-testid='stVerticalBlock']:has(.svc-cat-{char_key}) .stButton > button:hover {{",
            f"  border-color: {accent} !important;",
            f"  background: var(--salva-primary-soft) !important;",
            f"  color: var(--salva-text) !important;",
            f"  -webkit-text-fill-color: var(--salva-text) !important;",
            f"}}",
            f"div[data-testid='column']:has(.svc-cat-{char_key}) .stButton > button:hover::before,",
            f"div[data-testid='stVerticalBlock']:has(.svc-cat-{char_key}) .stButton > button:hover::before {{",
            f"  animation-duration: 2.5s !important;",
            f"}}",
            f"div[data-testid='column']:has(.svc-cat-{char_key}) .stButton > button p,",
            f"div[data-testid='stVerticalBlock']:has(.svc-cat-{char_key}) .stButton > button p {{",
            f"  margin: 0 !important; color: var(--salva-text) !important;",
            f"  -webkit-text-fill-color: var(--salva-text) !important;",
            f"  white-space: nowrap !important; overflow: hidden !important;",
            f"  text-overflow: ellipsis !important;",
            f"}}",
        ])
    return f"<style>{''.join(rules)}</style>"


def _pick_category(key_prefix: str, categories, cols_n: int = 4) -> str | None:
    """Grilla compacta: un botón por categoría con ícono inline."""
    selected = None
    st.markdown(_service_category_css(categories), unsafe_allow_html=True)
    st.markdown('<span class="svc-cat-grid-root" aria-hidden="true"></span>', unsafe_allow_html=True)
    for row_start in range(0, len(categories), cols_n):
        row = categories[row_start : row_start + cols_n]
        cols = st.columns(cols_n)
        for col, (label, char_key, mapped, desc) in zip(cols, row):
            with col:
                st.markdown(
                    f'<span class="svc-cat-marker svc-cat-{char_key}" aria-hidden="true"></span>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    label,
                    key=f"service_{char_key}",
                    use_container_width=True,
                    type="secondary",
                    help=desc or label,
                ):
                    selected = mapped if mapped else "__all__"
    return selected


def _svg_img(path: Path, alt: str, css_class: str = "", size: int = 72) -> str:
    if path.is_file():
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        cls = f' class="{css_class}"' if css_class else ""
        return (
            f'<img{cls} src="data:image/svg+xml;base64,{b64}" '
            f'width="{size}" height="{size}" alt="{html.escape(alt)}"/>'
        )
    return f'<div class="avatar-fallback">{html.escape(alt[:1])}</div>'


def form_category_picker(key_prefix: str = "fs") -> str | None:
    cats = [c for c in HOME_CATEGORIES if c[0] != "Ver todos"]
    return _pick_category(key_prefix, cats, 4)


def category_selector(key_prefix: str = "cat") -> str | None:
    st.markdown('<p class="section-title">¿Qué necesitás resolver?</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="body-text">Elegí un servicio y SALVA te ayuda con el resto.</p>',
        unsafe_allow_html=True,
    )
    return _pick_category(key_prefix, HOME_CATEGORIES, 4)


def empty_state(icon_key: str, title: str, text: str, button_label: str, button_key: str, salvita_state: str = "neutral") -> bool:
    from services.salvita import salvita_html

    icon = ICONS.get(icon_key, ICONS["empty"])
    st.markdown(
        f'<div class="empty-state fade-in">'
        f'{salvita_html(salvita_state, text[:80] if salvita_state == "neutral" else "")}'
        f'<div class="empty-icon-wrap">{icon}</div>'
        f'<div class="empty-title">{html.escape(title)}</div>'
        f'<div class="empty-text">{html.escape(text)}</div></div>',
        unsafe_allow_html=True,
    )
    return st.button(button_label, type="primary", use_container_width=True, key=button_key)


def hero_visual_composition() -> None:
    sym_path = SYMBOL_WHITE
    sym = _svg_img(sym_path, "SALVA", "hero-symbol-inline", 28) if sym_path.is_file() else ""
    avatar = avatar_img_html({"id": "PRO001", "name": "María González", "specialty": "Plomera", "photo_url": "assets/professionals/pro001.jpg"}, 72)
    st.markdown(
        f'<div class="hero-visual fade-in">'
        f'<div class="hero-pro-card">'
        f'{avatar}'
        f'<div><strong>María González</strong><br/>'
        f'<span class="support-text">Plomera · 4.9</span><br/>'
        f'<span class="chip-success">Identidad verificada</span> '
        f'<span class="chip-eta">Llega en 25 min</span></div></div>'
        f'<div class="hero-price-tag">Desde $85.000 · Precio orientativo</div>'
        f'<p class="support-text">Profesional verificada · 48 trabajos en tu zona</p>'
        f'<div class="promo-blue">{sym}<span>Tu hogar está resuelto y protegido</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def benefit_cards() -> None:
    cards = "".join(
        f'<div class="benefit-card salva-card-hover">'
        f'<div class="benefit-icon">{ICONS.get(icon_key, "")}</div>'
        f"<strong>{html.escape(title)}</strong>"
        f"<span>{html.escape(desc)}</span></div>"
        for icon_key, title, desc in BENEFITS
    )
    st.markdown(
        f'<p class="section-title">Todo resuelto desde un solo lugar</p>'
        f'<div class="benefit-grid">{cards}</div>',
        unsafe_allow_html=True,
    )


def render_flow_indicator(step: int, steps: list[str]) -> None:
    parts = []
    for i, label in enumerate(steps, 1):
        cls = "step-active" if i == step else ("step-done" if i < step else "step-pending")
        prefix = "✓ " if i < step else (f"{i}. " if i == step else "")
        parts.append(f'<span class="{cls}">{prefix}{html.escape(label)}</span>')
    st.markdown(f'<div class="status-track fade-in">{"".join(parts)}</div>', unsafe_allow_html=True)


def service_icon_html(category: str) -> str:
    key = SERVICE_ICON_KEY.get(category, "todos")
    return character_img_html(key, 32, f"svc-character svc-{key}")


def diagnosis_box_html(diagnosis: dict) -> str:
    from services.formatting import format_ars as fa
    return (
        f'<div class="diagnosis-box fade-in">'
        f'<p class="form-step-num">Diagnóstico orientativo del prototipo</p>'
        f'<p><strong>Problema:</strong> {html.escape(str(diagnosis.get("problem_reported", "")))}</p>'
        f'<p><strong>Oficio:</strong> {html.escape(str(diagnosis.get("recommended_trade", "")))} · '
        f'<strong>Urgencia:</strong> {html.escape(str(diagnosis.get("urgency", "")))}</p>'
        f'<p><strong>Rango:</strong> {fa(diagnosis.get("price_range_low", 0))} – {fa(diagnosis.get("price_range_high", 0))}</p>'
        f'<p><strong>Profesionales en tu zona:</strong> {html.escape(str(diagnosis.get("professionals_available", 0)))}</p>'
        f'</div>'
    )


def timeline_card(category: str, date_str: str, pro: str, price: str, rating: str, guarantee: str) -> None:
    icon = service_icon_html(category)
    st.markdown(
        f'<div class="timeline-card salva-card-hover">'
        f'<div class="timeline-row">'
        f'<div class="timeline-left">{icon}<strong>{html.escape(category)}</strong></div>'
        f'<span class="support-text">{html.escape(date_str)}</span></div>'
        f'<p class="support-text">{html.escape(pro)} · {html.escape(price)}</p>'
        f'<span class="chip-success">{html.escape(rating)}</span> '
        f'<span class="support-text">{html.escape(guarantee)}</span></div>',
        unsafe_allow_html=True,
    )


def goal_card_html(name: str, saved: float, target: float, pct: float, target_date: str) -> str:
    return (
        f'<div class="salva-card salva-card-hover" style="margin-bottom:0.75rem">'
        f'<strong>{html.escape(name)}</strong>'
        f'<p class="support-text">{format_ars(saved)} de {format_ars(target)} · {pct:.0f}%</p>'
        f'<div class="progress-bar-bg"><div class="progress-bar-fill" style="width:{min(pct,100):.0f}%"></div></div>'
        f'<p class="support-text">Objetivo: {html.escape(target_date)}</p></div>'
    )


def badges_html(pro: dict) -> str:
    tip = html.escape(BADGE_TOOLTIP)
    parts = []
    if pro.get("verified"):
        parts.append(f'<span class="badge badge-verified" title="{tip}">Profesional verificado</span>')
    if pro.get("identity_verified"):
        parts.append(f'<span class="badge badge-identity" title="{tip}">Identidad verificada</span>')
    if pro.get("matricula_verified"):
        parts.append(f'<span class="badge badge-matricula" title="{tip}">Matrícula verificada</span>')
    return " ".join(parts) if parts else f'<span class="badge badge-pending" title="{tip}">En revisión</span>'


def review_html(name: str, rating: float, comment: str, hood: str) -> str:
    stars = "★" * int(rating)
    return (
        f'<div class="review-item">'
        f'<strong>{html.escape(name)}</strong> · <span class="review-stars">{stars}</span>'
        f'<p class="review-text">&ldquo;{html.escape(comment)}&rdquo;</p>'
        f'<span class="review-meta">{html.escape(hood)}</span></div>'
    )


def pro_card_html(pro: dict, zone_label: str, hood_jobs: int, eta: str, price: float, reviews_html: str) -> str:
    name = html.escape(str(pro["name"]))
    specialty = html.escape(str(pro.get("specialty", "")))
    city = html.escape(str(pro.get("city", "")))
    province = html.escape(str(pro.get("province", "")))
    price_type = html.escape(str(pro.get("price_type", "Precio orientativo")))
    vreviews = int(pro.get("verified_reviews", 0))
    avatar = avatar_img_html(pro)
    coverage = f"{city}, {province}" if city else zone_label
    reviews_block = reviews_html if reviews_html else '<p class="no-reviews">Sin reseñas disponibles.</p>'
    return (
        f'<div class="pro-marketplace-card salva-card-hover fade-in">'
        f'<div class="pro-card-top">{avatar}'
        f'<div class="pro-card-main"><h3 class="pro-name">{name}</h3>'
        f'<p class="pro-specialty">{specialty}</p>'
        f'<div class="badge-row">{badges_html(pro)}</div>'
        f'<div class="pro-stats-row">'
        f'<span>{pro.get("rating", "—")} ★</span>'
        f'<span>{vreviews} reseñas</span>'
        f'<span>{pro.get("completed_jobs", 0)} trabajos</span></div>'
        f'<div class="pro-highlights">'
        f'<span class="highlight-chip">{hood_jobs} trabajos en tu zona</span>'
        f'<span class="highlight-chip eta">Llegada: {html.escape(eta)}</span>'
        f'<span class="highlight-chip">{coverage}</span></div>'
        f'<div class="pro-price-row">'
        f'<span class="pro-price">{format_ars(price)}</span>'
        f'<span class="pro-price-label">{price_type}</span></div></div></div>'
        f'<div class="pro-reviews">{reviews_block}</div>'
        f'</div>'
    )


def booking_pending_receipt_html(booking: dict, pro: dict, amount: float, appt_label: str, location: str) -> str:
    from services.branding import logo_header_html
    logo = logo_header_html()
    avatar = avatar_img_html(pro, 56)
    chat_on = str(booking.get("chat_enabled", "")).lower() in ("true", "1", "yes")
    return (
        f'<div class="receipt-card fade-in receipt-pending">'
        f'<div class="receipt-logo">{logo}</div>'
        f'<div class="receipt-clock">🕐</div>'
        f'<p class="receipt-status-badge pending">Turno reservado · Pago pendiente</p>'
        f'<h2 class="receipt-title">Tu turno quedó reservado</h2>'
        f'<p class="support-text" style="text-align:center">Para confirmar definitivamente la reserva, completá el pago.</p>'
        f'<p class="support-text" style="text-align:center">Conservaremos este turno durante 15 minutos.</p>'
        f'<p class="receipt-id">{html.escape(booking["id"])}</p>'
        f'<hr class="receipt-divider"/>'
        f'<div class="receipt-pro">{avatar}<div><strong>{html.escape(pro.get("name",""))}</strong>'
        f'<br/><span class="support-text">{html.escape(booking.get("service_type",""))}</span></div></div>'
        f'<p><strong>Turno:</strong> {html.escape(appt_label)}</p>'
        f'<p><strong>Ubicación:</strong> {html.escape(location)}</p>'
        f'<p><strong>Monto:</strong> {format_ars(amount)} · {html.escape(pro.get("price_type",""))}</p>'
        f'<p><strong>Pago:</strong> Pendiente</p>'
        f'<p><strong>Garantía:</strong> Se activa al confirmar el pago.</p>'
        f'<p><strong>Chat:</strong> {"Habilitado" if chat_on else "Se habilita al confirmar el pago"}</p>'
        f'</div>'
    )


def booking_confirmed_receipt_html(booking: dict, pro: dict, amount: float, appt_label: str, location: str) -> str:
    from services.branding import logo_header_html
    logo = logo_header_html()
    avatar = avatar_img_html(pro, 56)
    return (
        f'<div class="receipt-card fade-in success-pop">'
        f'<div class="receipt-logo">{logo}</div>'
        f'<div class="receipt-check anim-check">✓</div>'
        f'<h2 class="receipt-title">Reserva confirmada</h2>'
        f'<p class="support-text" style="text-align:center">Tu pago fue confirmado y el profesional ya recibió la reserva.</p>'
        f'<p class="receipt-id">{html.escape(booking["id"])}</p>'
        f'<hr class="receipt-divider"/>'
        f'<div class="receipt-pro">{avatar}<div><strong>{html.escape(pro.get("name",""))}</strong>'
        f'<br/><span class="support-text">{html.escape(booking.get("service_type",""))}</span></div></div>'
        f'<p><strong>Turno:</strong> {html.escape(appt_label)}</p>'
        f'<p><strong>Ubicación:</strong> {html.escape(location)}</p>'
        f'<p><strong>Monto:</strong> {format_ars(amount)}</p>'
        f'<p><strong>Pago:</strong> {html.escape(booking.get("payment_method",""))} · {html.escape(booking.get("card_brand",""))} ··{html.escape(booking.get("payment_last_four",""))}</p>'
        f'<p><strong>Referencia:</strong> {html.escape(booking.get("payment_reference",""))}</p>'
        f'<p><strong>Garantía:</strong> Cobertura activa</p>'
        f'<p><strong>Chat:</strong> Habilitado</p>'
        f'<p class="support-text">Confirmado: {html.escape(booking.get("confirmed_at", booking.get("paid_at","")))}</p>'
        f'</div>'
    )


def booking_receipt_html(booking: dict, pro: dict, amount: float, appt_label: str, location: str) -> str:
    if booking.get("payment_status") == "Pago confirmado":
        return booking_confirmed_receipt_html(booking, pro, amount, appt_label, location)
    return booking_pending_receipt_html(booking, pro, amount, appt_label, location)


def payment_receipt_html(booking: dict, amount: float) -> str:
    return (
        f'<div class="receipt-card fade-in success-pop">'
        f'<div class="receipt-check anim-check">✓</div>'
        f'<h2 class="receipt-title">Pago confirmado</h2>'
        f'<p class="receipt-id">{html.escape(booking["id"])}</p>'
        f'<hr class="receipt-divider"/>'
        f'<p><strong>Monto:</strong> {format_ars(amount)}</p>'
        f'<p><strong>Método:</strong> {html.escape(booking.get("payment_method",""))}</p>'
        f'<p><strong>Tarjeta:</strong> {html.escape(booking.get("card_brand",""))} ··{html.escape(booking.get("payment_last_four",""))}</p>'
        f'<p><strong>Referencia:</strong> {html.escape(booking.get("payment_reference",""))}</p>'
        f'<p class="support-text">{html.escape(booking.get("paid_at",""))}</p>'
        f'</div>'
    )


def tracking_road_html(
    current_status: str, flow: list[str], service_type: str = "", pro: dict | None = None,
) -> str:
    legacy = {"Reserva confirmada": "Pago confirmado"}
    current = legacy.get(current_status, current_status)
    idx = flow.index(current) if current in flow else 0
    positions = [4, 12, 38, 72, 86, 92]
    pct = positions[min(idx, len(positions) - 1)]
    fill_pct = pct
    stage_icons = ["📅", "✓", "🚐", "🏠", "🔧", "✨"]
    markers = ""
    for i, status in enumerate(flow):
        if i < idx:
            cls = "road-marker done"
        elif i == idx:
            cls = "road-marker active"
        else:
            cls = "road-marker pending"
        icon = stage_icons[i] if i < len(stage_icons) else "•"
        markers += (
            f'<div class="{cls}"><span class="road-stage-icon">{icon}</span>'
            f'<span class="road-dot"></span>'
            f'<span class="road-label">{html.escape(status)}</span></div>'
        )
    if pro:
        traveller = avatar_img_html(pro, 36).replace('class="', 'class="road-pro-avatar ')
    else:
        traveller = '<span class="road-pro-traveller" title="Profesional">🚐</span>'
    work = '<span class="road-work-tool">🔧</span>' if idx >= 4 else ""
    house_cls = "road-house-fixed"
    if idx >= 5:
        house_cls += " road-house-done"
    house = f'<div class="{house_cls}" title="Tu hogar">🏠✨</div>' if idx >= 5 else f'<div class="{house_cls}" title="Tu hogar">🏠</div>'
    return (
        f'<div class="tracking-road-v2 fade-in">'
        f'<div class="road-scene road-scene-ltr">'
        f'<div class="road-track-v2">'
        f'<div class="road-fill" style="width:{fill_pct}%"></div>'
        f'<div class="road-traveller-wrap" style="left:{pct}%">{traveller}{work}</div>'
        f'</div>'
        f'{house}'
        f'</div>'
        f'<div class="road-markers">{markers}</div>'
        f'<p class="road-current"><strong>Estado actual:</strong> {html.escape(current)}</p>'
        f'</div>'
    )


def card_brands_html(active: str = "") -> str:
    brands = ["Visa", "Mastercard"]
    parts = []
    for b in brands:
        cls = "card-brand active" if b == active else "card-brand"
        parts.append(f'<span class="{cls}">{html.escape(b)}</span>')
    return f'<div class="card-brands">{"".join(parts)}</div>'


RATING_LABELS = {1: "Muy mala", 2: "Mala", 3: "Regular", 4: "Muy buena", 5: "Excelente"}


def render_star_rating(booking_id: str) -> int | None:
    key = f"stars_{booking_id}"
    val_key = f"rating_val_{booking_id}"
    if hasattr(st, "feedback"):
        sel = st.feedback("stars", key=key)
        if sel is not None:
            st.session_state[val_key] = int(sel) + 1
    rating = st.session_state.get(val_key)
    if rating:
        st.markdown(
            f'<p class="star-label-active">Calificación: {rating}/5 — {html.escape(RATING_LABELS.get(rating, ""))}</p>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("Seleccioná de 1 a 5 estrellas")
    return rating


def completed_service_receipt_html(booking: dict, pro: dict, rating: int, comment: str, work: str) -> str:
    avatar = avatar_img_html(pro, 56)
    return (
        f'<div class="receipt-card fade-in success-pop">'
        f'<div class="receipt-check anim-check">✓</div>'
        f'<h2 class="receipt-title">Servicio completado</h2>'
        f'<p class="support-text" style="text-align:center">¡Gracias! Tu calificación fue enviada.</p>'
        f'<div class="receipt-pro">{avatar}<div><strong>{html.escape(pro.get("name",""))}</strong></div></div>'
        f'<p><strong>Trabajo:</strong> {html.escape(work)}</p>'
        f'<p><strong>Calificación:</strong> {"★" * rating} ({rating}/5)</p>'
        f'<p><strong>Comentario:</strong> {html.escape(comment)}</p>'
        f'<p class="support-text">{html.escape(booking.get("id",""))}</p></div>'
    )


def render_chat_panel(booking: dict, pro: dict) -> None:
    from services.chat import USER_QUICK_MESSAGES, add_message, load_messages, seed_booking_chat, simulate_pro_reply

    bid = booking["id"]
    paid = booking.get("payment_status") == "Pago confirmado"
    if not paid and str(booking.get("chat_enabled", "")).lower() not in ("true", "1", "yes"):
        st.info("El chat se habilitará cuando confirmes la reserva.")
        return
    seed_booking_chat(bid, pro.get("name", "Profesional"), paid=paid)
    st.caption("Para tu seguridad y garantía, mantené la conversación dentro de SALVA.")
    pro_avatar = avatar_img_html(pro, 36)
    st.markdown(
        f'<div class="chat-header">{pro_avatar}<div><strong>{html.escape(pro.get("name",""))}</strong>'
        f'<br/><span class="support-text">{html.escape(booking.get("service_type",""))} · {html.escape(bid)}</span></div></div>',
        unsafe_allow_html=True,
    )
    msgs = load_messages(bid)
    chat_html = '<div class="chat-thread">'
    for _, m in msgs.iterrows():
        sender = html.escape(str(m["sender_name"]))
        text = html.escape(str(m["message_text"]))
        ts = html.escape(str(m["sent_at"]))
        read = " · Leído" if str(m.get("read_at", "")).strip() else ""
        if m["sender_type"] == "system":
            chat_html += f'<div class="chat-bubble chat-system"><p>{text}</p><span class="chat-ts">{ts}</span></div>'
        elif m["sender_type"] == "professional":
            chat_html += (
                f'<div class="chat-bubble chat-pro">{pro_avatar}'
                f'<div><strong>{sender}</strong><p>{text}</p><span class="chat-ts">{ts}{read}</span></div></div>'
            )
        else:
            chat_html += f'<div class="chat-bubble chat-user"><strong>{sender}</strong><p>{text}</p><span class="chat-ts">{ts}{read}</span></div>'
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)
    st.markdown("**Mensajes rápidos**")
    qcols = st.columns(2)
    for i, qm in enumerate(USER_QUICK_MESSAGES):
        with qcols[i % 2]:
            if st.button(qm, key=f"quick_{bid}_{i}", use_container_width=True):
                add_message(bid, "customer", booking.get("customer_name", "Cliente"), qm)
                simulate_pro_reply(bid, pro.get("name", "Profesional"), qm)
                st.rerun()
    with st.form(f"chat_form_{bid}", clear_on_submit=True):
        text = st.text_input("Escribí un mensaje", key=f"chat_input_{bid}")
        attach = st.file_uploader("Adjuntar foto (opcional)", type=["jpg", "png"], key=f"chat_attach_{bid}")
        if st.form_submit_button("Enviar", type="primary", use_container_width=True):
            if text.strip():
                att = attach.name if attach else ""
                add_message(bid, "customer", booking.get("customer_name", "Cliente"), text.strip(), attachment_name=att)
                simulate_pro_reply(bid, pro.get("name", "Profesional"), text.strip())
                st.rerun()
