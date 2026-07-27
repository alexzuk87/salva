"""SALVA Pay."""

import streamlit as st

from services.formatting import format_ars
from services.salva_pay import pay_dashboard_metrics, payment_summary, recent_transactions, simulate_financing


def render_financing_simulator(key_prefix: str = "pay") -> None:
    st.markdown("#### Simulador de financiación")
    st.markdown('<div class="sim-banner">Simulación académica. No constituye una oferta de crédito.</div>', unsafe_allow_html=True)
    amount = st.number_input(
        "Monto del servicio ($)",
        min_value=1000,
        value=85000,
        step=5000,
        key=f"{key_prefix}_financing_amount",
    )
    inst = st.selectbox("Cuotas", [1, 3, 6, 12], key=f"{key_prefix}_financing_installments")
    sim = simulate_financing(float(amount), inst)
    st.markdown(f"**Cuota mensual simulada:** {format_ars(sim['monthly'])}")
    st.markdown(f"**Total simulado:** {format_ars(sim['total'])} ({sim['rate_label']})")


def render() -> None:
    st.markdown('<p class="section-title">SALVA Pay</p>', unsafe_allow_html=True)
    st.markdown('<p class="body-text">Organizá y pagá los gastos de tu hogar desde un solo lugar.</p>', unsafe_allow_html=True)

    m = pay_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pagado", m["pagado"])
    c2.metric("Pendiente", m["pendiente"])
    c3.metric("Gastos del mes", m["mes"])
    c4.metric("Ahorros Objetivos", m["ahorros_objetivos"])

    with st.container(border=True):
        render_financing_simulator()

    st.markdown('<div class="salva-card">', unsafe_allow_html=True)
    st.markdown("#### Medios de pago disponibles")
    for m in ["Tarjeta de crédito", "Transferencia bancaria / alias", "Financiación simulada SALVA Pay"]:
        st.markdown(f"- {m}")
    st.markdown("</div>", unsafe_allow_html=True)

    txs = recent_transactions()
    st.markdown("#### Transacciones recientes")
    if txs.empty:
        st.caption("Aún no hay transacciones registradas.")
    else:
        for _, t in txs.iterrows():
            st.markdown(
                f'<div class="timeline-card"><strong>{t["id"]}</strong> · {t["service_type"]}<br/>'
                f'<span style="color:#687078">{t["professional_name"]} · {format_ars(t["amount"])} · {t["payment_status"]}</span></div>',
                unsafe_allow_html=True,
            )

    s = payment_summary()
    st.caption(f"{s['pending_count']} pago(s) pendiente(s) · {s['completed_count']} confirmado(s)")
