"""Chat interno SALVA (simulado)."""

from datetime import datetime

import pandas as pd

from services.data_store import CHAT_MESSAGES_FILE, read_csv, write_csv

CHAT_COLUMNS = [
    "message_id", "booking_id", "sender_type", "sender_name",
    "message_text", "sent_at", "read_at", "message_type", "attachment_name",
]

USER_QUICK_MESSAGES = [
    "Estoy en el domicilio",
    "Te envío una foto del problema",
    "¿Me avisás cuando estés cerca?",
    "Necesito agregar un detalle",
    "¿Podemos confirmar el horario?",
    "¿Necesitás alguna indicación para llegar?",
]

PRO_REPLIES = {
    "foto": "¿Podés enviarme una foto del problema?",
    "cerca": "Estoy a pocos minutos del domicilio.",
    "camino": "Ya estoy en camino. Te aviso cuando esté cerca.",
    "domicilio": "Llegué al domicilio.",
    "detalle": "Necesito confirmar un detalle antes de comenzar.",
    "default": "Recibido. Te respondo en breve con la información.",
}

SYSTEM_MESSAGES = {
    "Turno reservado": "Turno reservado · Pago pendiente",
    "Reserva confirmada": "Reserva confirmada",
    "Pago confirmado": "Pago confirmado",
    "Profesional en camino": "El profesional está en camino",
    "Profesional en el domicilio": "El profesional llegó al domicilio",
    "Servicio finalizado": "El servicio finalizó",
}


def load_messages(booking_id: str) -> pd.DataFrame:
    df = read_csv(CHAT_MESSAGES_FILE, CHAT_COLUMNS)
    if df.empty:
        return df
    return df[df["booking_id"] == booking_id].sort_values("sent_at").reset_index(drop=True)


def _next_message_id(df: pd.DataFrame) -> str:
    if df.empty or "message_id" not in df.columns:
        return "MSG001"
    nums = df["message_id"].str.replace("MSG", "", regex=False).astype(int)
    return f"MSG{nums.max() + 1:03d}"


def add_message(
    booking_id: str,
    sender_type: str,
    sender_name: str,
    message_text: str,
    message_type: str = "text",
    attachment_name: str = "",
) -> dict:
    df = read_csv(CHAT_MESSAGES_FILE, CHAT_COLUMNS)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = {
        "message_id": _next_message_id(df),
        "booking_id": booking_id,
        "sender_type": sender_type,
        "sender_name": sender_name,
        "message_text": message_text.strip(),
        "sent_at": now,
        "read_at": "",
        "message_type": message_type,
        "attachment_name": attachment_name,
    }
    write_csv(CHAT_MESSAGES_FILE, pd.concat([df, pd.DataFrame([row])], ignore_index=True))
    return row


def add_system_message(booking_id: str, status_key: str) -> None:
    text = SYSTEM_MESSAGES.get(status_key, status_key)
    existing = load_messages(booking_id)
    if not existing.empty and (existing["message_text"] == text).any():
        return
    add_message(booking_id, "system", "SALVA", text, message_type="system")


def add_professional_message(booking_id: str, pro_name: str, text: str) -> None:
    add_message(booking_id, "professional", pro_name, text)


def seed_booking_chat(booking_id: str, pro_name: str, paid: bool = False) -> None:
    msgs = load_messages(booking_id)
    if not msgs.empty:
        return
    if paid:
        add_system_message(booking_id, "Reserva confirmada")
        add_professional_message(
            booking_id, pro_name,
            "Hola, confirmé tu reserva. Te escribo por acá para coordinar los detalles.",
        )
    else:
        add_system_message(booking_id, "Turno reservado")


def simulate_pro_reply(booking_id: str, pro_name: str, user_text: str) -> None:
    lower = user_text.lower()
    if "foto" in lower:
        reply = PRO_REPLIES["foto"]
    elif "cerca" in lower or "avis" in lower:
        reply = PRO_REPLIES["cerca"]
    elif "horario" in lower or "confirm" in lower:
        reply = PRO_REPLIES["detalle"]
    elif "indicación" in lower or "llegar" in lower:
        reply = "Gracias, con esa referencia llego sin problemas."
    elif "detalle" in lower:
        reply = PRO_REPLIES["detalle"]
    else:
        reply = PRO_REPLIES["default"]
    add_professional_message(booking_id, pro_name, reply)


def pro_message_for_status(status: str, pro_name: str) -> str | None:
    mapping = {
        "Profesional en camino": PRO_REPLIES["camino"],
        "Profesional en el domicilio": PRO_REPLIES["domicilio"],
    }
    return mapping.get(status)
