"""Gestión de reservas con migración compatible."""

from datetime import datetime, timedelta

import pandas as pd

from services.data_store import BOOKINGS_FILE, next_id, read_csv, write_csv
from services.locations import legacy_location
from services.professionals import estimate_price, get_professional
from services.scheduling import format_appointment

BOOKING_COLUMNS = [
    "id", "customer_name", "province", "locality", "neighborhood", "address",
    "apartment", "location_reference", "location", "service_type",
    "problem_description", "urgency", "preferred_date", "preferred_time",
    "appointment_date", "appointment_time", "professional_id", "professional_name",
    "price_type", "initial_price", "approved_price", "estimated_arrival",
    "booking_status", "service_status", "payment_method", "payment_status",
    "payment_last_four", "card_brand", "payment_reference", "paid_at",
    "created_at", "confirmed_at", "completed_at", "guarantee_status",
    "warranty_until", "price_change_proposed", "price_change_reason",
    "terms_accepted", "work_completed", "chat_enabled",
]

PAYMENT_PENDING = "Pago pendiente"
PAYMENT_CONFIRMED = "Pago confirmado"

BOOKING_TURNO_RESERVADO = "Turno reservado"
BOOKING_RESERVA_CONFIRMADA = "Reserva confirmada"
BOOKING_EN_SEGUIMIENTO = "En seguimiento"
BOOKING_FINALIZADA = "Servicio finalizado"
BOOKING_CANCELADA = "Cancelada"

SERVICE_STATUS_FLOW = [
    "Turno reservado",
    "Pago confirmado",
    "Profesional en camino",
    "Profesional en el domicilio",
    "Trabajo en curso",
    "Servicio finalizado",
]

FINAL_BOOKING_STATUSES = {
    BOOKING_FINALIZADA,
    "Completada",
    "Finalizada",
}
FINAL_SERVICE_STATUSES = {
    "Servicio finalizado",
    "Completado",
    "Finalizado",
}
CANCELLED_STATUSES = {BOOKING_CANCELADA, "Cancelado", "Cancelada"}


def _migrate_raw(path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    mapping = {
        "description": "problem_description",
        "status": "booking_status",
        "estimated_price": "initial_price",
    }
    for old, new in mapping.items():
        if old in raw.columns and new not in raw.columns:
            raw[new] = raw[old]
    if "location" in raw.columns and "address" not in raw.columns:
        raw["address"] = raw["location"]
    if "preferred_date" in raw.columns and "appointment_date" not in raw.columns:
        raw["appointment_date"] = raw["preferred_date"]
    if "preferred_time" in raw.columns and "appointment_time" not in raw.columns:
        raw["appointment_time"] = raw["preferred_time"]
    if "approved_price" not in raw.columns and "initial_price" in raw.columns:
        raw["approved_price"] = raw["initial_price"]
    if "service_status" not in raw.columns:
        raw["service_status"] = ""
    if "guarantee_status" not in raw.columns:
        raw["guarantee_status"] = "Sin reclamo"
    for col in BOOKING_COLUMNS:
        if col not in raw.columns:
            raw[col] = ""
    return raw[BOOKING_COLUMNS]


def load_bookings() -> pd.DataFrame:
    if BOOKINGS_FILE.exists():
        header = set(pd.read_csv(BOOKINGS_FILE, nrows=0).columns)
        needs = {"problem_description", "appointment_date", "province", "address"}
        if not needs.issubset(header) or ("description" in header and "problem_description" not in header):
            df = _migrate_raw(BOOKINGS_FILE)
            write_csv(BOOKINGS_FILE, df)
            return df
    return read_csv(BOOKINGS_FILE, BOOKING_COLUMNS)


def create_booking(**kwargs) -> dict:
    pro = get_professional(kwargs["professional_id"])
    if not pro:
        raise ValueError("Profesional no encontrado")

    df = load_bookings()
    booking_id = next_id(df, "BK")
    price = estimate_price(pro["base_price"], kwargs["urgency"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    appt_date = kwargs.get("appointment_date") or kwargs.get("preferred_date", "")
    appt_time = kwargs.get("appointment_time") or kwargs.get("preferred_time", "")

    row = {
        "id": booking_id,
        "customer_name": kwargs["customer_name"],
        "province": kwargs.get("province", ""),
        "locality": kwargs.get("locality", ""),
        "neighborhood": kwargs.get("neighborhood", ""),
        "address": kwargs.get("address") or kwargs.get("location", ""),
        "apartment": kwargs.get("apartment", ""),
        "location_reference": kwargs.get("location_reference", ""),
        "location": legacy_location({
            "address": kwargs.get("address") or kwargs.get("location", ""),
            "neighborhood": kwargs.get("neighborhood", ""),
            "locality": kwargs.get("locality", ""),
            "province": kwargs.get("province", ""),
            "apartment": kwargs.get("apartment", ""),
        }),
        "service_type": kwargs["service_type"],
        "problem_description": kwargs["problem_description"],
        "urgency": kwargs["urgency"],
        "preferred_date": appt_date,
        "preferred_time": appt_time,
        "appointment_date": appt_date,
        "appointment_time": appt_time,
        "professional_id": kwargs["professional_id"],
        "professional_name": pro["name"],
        "price_type": pro.get("price_type", "Precio orientativo"),
        "initial_price": price,
        "approved_price": price,
        "estimated_arrival": kwargs.get("estimated_arrival", ""),
        "booking_status": BOOKING_TURNO_RESERVADO,
        "service_status": "Turno reservado",
        "payment_method": "",
        "payment_status": PAYMENT_PENDING,
        "payment_last_four": "",
        "card_brand": "",
        "payment_reference": "",
        "paid_at": "",
        "created_at": now,
        "confirmed_at": "",
        "completed_at": "",
        "guarantee_status": "Se activa al confirmar el pago",
        "warranty_until": "",
        "price_change_proposed": "",
        "price_change_reason": "",
        "terms_accepted": "True" if kwargs.get("terms_accepted") else "False",
        "work_completed": "",
        "chat_enabled": "False",
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_csv(BOOKINGS_FILE, df)
    return row


def get_booking(booking_id: str) -> dict | None:
    df = load_bookings()
    match = df[df["id"] == booking_id]
    return match.iloc[0].to_dict() if not match.empty else None


def update_booking(booking_id: str, **fields) -> dict | None:
    df = load_bookings()
    idx = df[df["id"] == booking_id].index
    if idx.empty:
        return None
    for key, val in fields.items():
        if key in BOOKING_COLUMNS:
            df.loc[idx, key] = str(val) if val is not None else ""
    write_csv(BOOKINGS_FILE, df)
    return df.loc[idx[0]].to_dict()


def list_bookings(customer_name: str | None = None) -> pd.DataFrame:
    df = load_bookings()
    if customer_name:
        df = df[df["customer_name"].str.lower() == customer_name.lower()]
    return df.sort_values("created_at", ascending=False).reset_index(drop=True) if not df.empty else df


def split_bookings_for_home(df: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Clasifica reservas para Mi hogar contemplando estados actuales y legacy."""
    source = load_bookings() if df is None else df.copy()
    empty = source.iloc[0:0].copy()
    if source.empty:
        return {"en_curso": empty, "proximos": empty, "finalizados": empty}

    booking_status = source["booking_status"].fillna("")
    service_status = source["service_status"].fillna("")
    payment_status = source["payment_status"].fillna("")
    cancelled = booking_status.isin(CANCELLED_STATUSES)
    finalized = booking_status.isin(FINAL_BOOKING_STATUSES) | service_status.isin(FINAL_SERVICE_STATUSES)
    paid = payment_status.eq(PAYMENT_CONFIRMED)
    in_progress = ~cancelled & ~finalized & paid
    upcoming = ~cancelled & ~finalized & ~in_progress

    return {
        "en_curso": source[in_progress].reset_index(drop=True),
        "proximos": source[upcoming].reset_index(drop=True),
        "finalizados": source[finalized].reset_index(drop=True),
    }


def flow_step_for_booking(booking: dict) -> int:
    """Paso de Servicios apropiado al reingresar desde Mi hogar."""
    if (
        booking.get("booking_status") in FINAL_BOOKING_STATUSES
        or booking.get("service_status") in FINAL_SERVICE_STATUSES
    ):
        return 6
    if booking.get("payment_status") == PAYMENT_CONFIRMED:
        return 5
    return 4


def advance_service_status(booking_id: str) -> dict | None:
    from services.chat import add_professional_message, add_system_message, pro_message_for_status

    booking = get_booking(booking_id)
    if not booking:
        return None
    flow = SERVICE_STATUS_FLOW
    current = booking.get("service_status") or flow[0]
    legacy = {"Reserva confirmada": "Pago confirmado"}
    if current in legacy:
        current = legacy[current]
    if current not in flow:
        current = flow[0]
    idx = flow.index(current)
    if idx >= len(flow) - 1:
        return booking
    nxt = flow[idx + 1]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    fields = {"service_status": nxt}
    if nxt == "Pago confirmado":
        fields["booking_status"] = BOOKING_RESERVA_CONFIRMADA
    elif nxt in ("Profesional en camino", "Profesional en el domicilio", "Trabajo en curso"):
        fields["booking_status"] = BOOKING_EN_SEGUIMIENTO
    elif nxt == "Servicio finalizado":
        fields["booking_status"] = BOOKING_FINALIZADA
        fields["completed_at"] = now
        fields["warranty_until"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    result = update_booking(booking_id, **fields)
    if nxt in SYSTEM_STATUS_KEYS:
        add_system_message(booking_id, nxt)
    pro_msg = pro_message_for_status(nxt, booking.get("professional_name", "Profesional"))
    if pro_msg:
        add_professional_message(booking_id, booking.get("professional_name", "Profesional"), pro_msg)
    return result


SYSTEM_STATUS_KEYS = {
    "Pago confirmado", "Profesional en camino", "Profesional en el domicilio", "Servicio finalizado",
}


def propose_price_change(booking_id: str, new_price: float, reason: str) -> dict | None:
    return update_booking(
        booking_id,
        price_change_proposed=str(new_price),
        price_change_reason=reason,
    )


def accept_price_change(booking_id: str) -> dict | None:
    booking = get_booking(booking_id)
    if not booking or not booking.get("price_change_proposed"):
        return booking
    return update_booking(
        booking_id,
        approved_price=booking["price_change_proposed"],
        price_change_proposed="",
        price_change_reason="",
    )


def appointment_label(booking: dict) -> str:
    return format_appointment(
        booking.get("appointment_date") or booking.get("preferred_date", ""),
        booking.get("appointment_time") or booking.get("preferred_time", ""),
    )
