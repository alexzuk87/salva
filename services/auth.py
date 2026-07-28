"""Autenticación OIDC nativa de Streamlit para SALVA."""

from typing import Any

import streamlit as st

from services.branding import logo_header_html


def _user_claim(name: str, default: str = "") -> str:
    """Lee claims OIDC sin asumir que el proveedor envía todos los campos."""
    try:
        value: Any = st.user.get(name, default)
    except (AttributeError, KeyError, TypeError):
        value = default
    if value is None:
        return default
    return str(value).strip()


def authenticated_user() -> dict[str, str]:
    """Devuelve únicamente los datos públicos requeridos de la identidad."""
    return {
        "sub": _user_claim("sub"),
        "email": _user_claim("email"),
        "name": _user_claim("name"),
        "picture": _user_claim("picture"),
    }


def is_logged_in() -> bool:
    try:
        return bool(st.user.is_logged_in)
    except (AttributeError, TypeError):
        return False


def require_login() -> bool:
    """Protege la aplicación y renderiza solamente el acceso si falta sesión."""
    if is_logged_in():
        st.session_state.auth_user = authenticated_user()
        return True

    st.markdown('<span class="salva-auth-marker" aria-hidden="true"></span>', unsafe_allow_html=True)
    st.markdown(logo_header_html(), unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<h1 class="salva-auth-title">Ingresá a SALVA</h1>', unsafe_allow_html=True)
        st.markdown(
            '<p class="body-text">Accedé de forma segura para solicitar servicios y '
            "administrar tu hogar desde un solo lugar.</p>",
            unsafe_allow_html=True,
        )
        st.button(
            "Continuar con Google",
            key="salva_google_login",
            type="primary",
            use_container_width=True,
            on_click=st.login,
        )
    st.caption("SALVA usa Google únicamente para verificar tu identidad.")
    return False


def render_user_session() -> None:
    """Muestra la identidad activa y permite cerrar la sesión desde Mi hogar."""
    user = authenticated_user()
    if user["picture"]:
        st.image(user["picture"], width=56)
    st.markdown(f"**{user['name'] or 'Cuenta de Google'}**")
    if user["email"]:
        st.caption(user["email"])
    if st.button("Cerrar sesión", key="salva_logout", use_container_width=True):
        st.logout()
