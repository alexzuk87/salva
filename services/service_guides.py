"""Guías dinámicas por categoría de servicio (preguntas orientativas)."""

from __future__ import annotations

from services.service_categories import CATEGORY_ORDER, category_key, category_label

# Guías indexadas por clave estable (no por label ni por valor interno).
SERVICE_GUIDES: dict[str, dict[str, object]] = {
    "plomeria": {
        "placeholder": "Por ejemplo: hay una pérdida debajo de la pileta de la cocina desde ayer.",
        "questions": [
            "¿Hay pérdida de agua?",
            "¿Dónde se encuentra?",
            "¿Podés cerrar la llave de paso?",
            "¿Desde cuándo ocurre?",
        ],
    },
    "electricidad": {
        "placeholder": "Por ejemplo: saltó la térmica y no hay luz en el living desde esta mañana.",
        "questions": [
            "¿Hay corte total o parcial?",
            "¿Saltó la térmica o el disyuntor?",
            "¿Sentís olor a quemado o ves chispas?",
            "¿Qué ambiente o artefacto está afectado?",
        ],
    },
    "gas": {
        "placeholder": "Por ejemplo: la cocina no enciende bien y detecto olor leve cerca del artefacto.",
        "questions": [
            "¿Sentís olor a gas?",
            "¿El problema afecta cocina, calefón o estufa?",
            "¿El suministro está cerrado?",
        ],
        "warning": (
            "Si existe olor intenso a gas, cerrá la llave, ventilá y contactá "
            "al servicio de emergencia correspondiente."
        ),
    },
    "cerrajeria": {
        "placeholder": "Por ejemplo: la llave se rompió en la cerradura de la puerta de entrada.",
        "questions": [
            "¿Es una apertura, cambio o reparación?",
            "¿La puerta está cerrada?",
            "¿La llave quedó dentro o se rompió?",
            "¿Qué tipo de cerradura tiene?",
        ],
    },
    "limpieza": {
        "placeholder": "Por ejemplo: necesito una limpieza profunda de un departamento de 3 ambientes.",
        "questions": [
            "¿Qué tipo de inmueble es?",
            "¿Cuántos ambientes?",
            "¿Es limpieza general, profunda o posterior a una obra?",
            "¿Hay zonas que requieran atención especial?",
        ],
    },
    "pintura": {
        "placeholder": "Por ejemplo: quiero pintar una cocina de 3 × 4 metros, incluyendo el techo.",
        "questions": [
            "¿Qué ambiente o superficie querés pintar?",
            "¿Cuáles son sus medidas aproximadas?",
            "¿Hay humedad o reparaciones previas?",
            "¿Incluye techo, paredes o aberturas?",
        ],
    },
    "electrodomesticos": {
        "placeholder": "Por ejemplo: el lavarropas Samsung no centrifuga y muestra un código de error.",
        "questions": [
            "¿Qué artefacto es?",
            "¿Marca y modelo?",
            "¿Qué falla presenta?",
            "¿Enciende o muestra algún código de error?",
        ],
    },
    "jardineria": {
        "placeholder": "Por ejemplo: necesito poda y corte de césped en un jardín de unos 40 m².",
        "questions": [
            "¿Qué tamaño aproximado tiene el espacio?",
            "¿Necesitás poda, corte, mantenimiento o diseño?",
            "¿Hay árboles o plantas de gran tamaño?",
            "¿Se pueden retirar los residuos verdes?",
        ],
    },
    "albanileria": {
        "placeholder": "Por ejemplo: hay una grieta en la pared del patio y se desprende revoque.",
        "questions": [
            "¿Es reparación, construcción o terminación?",
            "¿Qué superficie o medida aproximada tiene?",
            "¿Hay humedad, grietas o desprendimientos?",
            "¿Se necesita retirar escombros?",
        ],
    },
    "aire": {
        "placeholder": "Por ejemplo: el split de 3000 frigorías enciende pero no enfría bien.",
        "questions": [
            "¿Es instalación, reparación o mantenimiento?",
            "¿Es split o equipo de ventana?",
            "¿Enciende y enfría?",
            "¿Conocés marca y capacidad?",
        ],
    },
    "carpinteria": {
        "placeholder": "Por ejemplo: necesito fabricar una puerta de placard a medida de 1,80 × 2,20 m.",
        "questions": [
            "¿Es reparación, fabricación o instalación?",
            "¿Qué mueble, puerta o abertura?",
            "¿Tenés medidas aproximadas?",
            "¿Qué material o terminación buscás?",
        ],
    },
}

_DEFAULT_GUIDE = {
    "placeholder": "Contanos con el mayor detalle posible qué necesitás resolver.",
    "questions": [
        "¿Qué problema querés resolver?",
        "¿Dónde se encuentra?",
        "¿Desde cuándo ocurre?",
        "¿Hay alguna urgencia o restricción de acceso?",
    ],
}


def guide_for_category(category_ref: str) -> dict[str, object]:
    """Obtiene guía por clave estable, etiqueta visible o valor interno."""
    key = category_key(category_ref)
    guide = SERVICE_GUIDES.get(key) or _DEFAULT_GUIDE
    return {
        "key": key,
        "label": category_label(category_ref) if category_ref else "",
        "placeholder": str(guide.get("placeholder", _DEFAULT_GUIDE["placeholder"])),
        "questions": list(guide.get("questions", _DEFAULT_GUIDE["questions"])),
        "warning": str(guide.get("warning", "") or ""),
    }


def render_category_guide(category_ref: str) -> None:
    """Renderiza preguntas orientativas (no obligatorias) para la categoría."""
    import streamlit as st

    guide = guide_for_category(category_ref)
    st.caption("Estas preguntas son orientativas. Podés responderlas en el texto libre.")
    for question in guide["questions"]:
        st.markdown(f"- {question}")
    warning = guide.get("warning") or ""
    if warning:
        st.warning(str(warning))


def assert_guides_cover_catalog() -> None:
    missing = [key for key in CATEGORY_ORDER if key not in SERVICE_GUIDES]
    if missing:
        raise AssertionError(f"Faltan guías para: {missing}")
