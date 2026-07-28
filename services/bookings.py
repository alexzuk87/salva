"""Gestión de reservas con migración compatible (seña 20% / saldo 80%)."""

from datetime import datetime, timedelta

import pandas as pd

from services.data_store import BOOKINGS_FILE, next_id, read_csv, write_csv
from services.locations import legacy_location
from services.pricing import DEPOSIT_PERCENTAGE, booking_totals, money_round, split_deposit
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
    # Seña / saldo (compatibles; se agregan al cargar CSV antiguos)
    "total_price", "deposit_percentage", "deposit_amount", "deposit_status",
    "deposit_paid_at", "deposit_payment_method", "remaining_amount",
    "remaining_status", "remaining_paid_at", "remaining_payment_method",
]

# Estados de pago (nuevos + legacy)
PAYMENT_PENDING = "Pago pendiente"  # legacy
PAYMENT_CONFIRMED = "Pago confirmado"  # legacy = pago completo
PAYMENT_DEPOSIT_PENDING = "seña_pendiente"
PAYMENT_DEPOSIT_CONFIRMED = "seña_confirmada"
PAYMENT_REMAINING_PENDING = "saldo_pendiente"
PAYMENT_COMPLETED = "pago_completado"

DEPOSIT_STATUS_PENDING = "pendiente"
DEPOSIT_STATUS_CONFIRMED = "confirmado"
REMAINING_STATUS_BLOCKED = "bloqueado"
REMAINING_STATUS_PENDING = "pendiente"
REMAINING_STATUS_CONFIRMED = "confirmado"

BOOKING_TURNO_RESERVADO = "Turno reservado"
BOOKING_RESERVA_CONFIRMADA = "Reserva confirmada"
BOOKING_EN_SEGUIMIENTO = "En seguimiento"
BOOKING_FINALIZADA = "Servicio finalizado"
BOOKING_CANCELADA = "Cancelada"

SERVICE_STATUS_FLOW = [
    "Seña confirmada",
    "Profesional en camino",
    "Profesional en el domicilio",
    "Trabajo en curso",
    "Servicio finalizado",
    "Saldo pendiente",
    "Pago completado",
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
    "Pago completado",
}
CANCELLED_STATUSES = {BOOKING_CANCELADA, "Cancelado", "Cancelada"}

_NEW_PAYMENT_COLS = {
    "total_price", "deposit_percentage", "deposit_amount", "deposit_status",
    "deposit_paid_at", "deposit_payment_method", "remaining_amount",
    "remaining_status", "remaining_paid_at", "remaining_payment_method",
}


def _backfill_payment_fields(row: dict) -> dict:
    """Completa columnas de seña/saldo para filas legacy sin romper datos."""
    total = money_round(row.get("total_price") or row.get("approved_price") or row.get("initial_price") or 0)
    pct = int(float(row.get("deposit_percentage") or DEPOSIT_PERCENTAGE) or DEPOSIT_PERCENTAGE)
    _, deposit, remaining = split_deposit(total, pct)

    if not str(row.get("total_price") or "").strip():
        row["total_price"] = str(total)
    if not str(row.get("deposit_percentage") or "").strip():
        row["deposit_percentage"] = str(pct)
    if not str(row.get("deposit_amount") or "").strip():
        row["deposit_amount"] = str(deposit)
    if not str(row.get("remaining_amount") or "").strip():
        row["remaining_amount"] = str(remaining)

    ps = str(row.get("payment_status") or "").strip()
    ds = str(row.get("deposit_status") or "").strip()
    rs = str(row.get("remaining_status") or "").strip()

    # Legacy: pago completo de una sola vez — completar columnas nuevas sin borrar el status original
    if ps == PAYMENT_CONFIRMED:
        if not ds:
            row["deposit_status"] = DEPOSIT_STATUS_CONFIRMED
        if not rs:
            row["remaining_status"] = REMAINING_STATUS_CONFIRMED
        if not str(row.get("deposit_paid_at") or "").strip():
            row["deposit_paid_at"] = row.get("paid_at") or row.get("confirmed_at") or ""
        if not str(row.get("remaining_paid_at") or "").strip():
            row["remaining_paid_at"] = row.get("paid_at") or row.get("confirmed_at") or ""
        if not str(row.get("deposit_payment_method") or "").strip():
            row["deposit_payment_method"] = row.get("payment_method") or ""
        if not str(row.get("remaining_payment_method") or "").strip():
            row["remaining_payment_method"] = row.get("payment_method") or ""
    elif ps in ("", PAYMENT_PENDING, PAYMENT_DEPOSIT_PENDING):
        if not ds:
            row["deposit_status"] = DEPOSIT_STATUS_PENDING
        if not rs:
            row["remaining_status"] = REMAINING_STATUS_BLOCKED
        if ps in ("", PAYMENT_PENDING):
            row["payment_status"] = PAYMENT_DEPOSIT_PENDING
    elif ps == PAYMENT_DEPOSIT_CONFIRMED:
        if not ds:
            row["deposit_status"] = DEPOSIT_STATUS_CONFIRMED
        if not rs:
            row["remaining_status"] = REMAINING_STATUS_BLOCKED
    elif ps == PAYMENT_REMAINING_PENDING:
        if not ds:
            row["deposit_status"] = DEPOSIT_STATUS_CONFIRMED
        if not rs:
            row["remaining_status"] = REMAINING_STATUS_PENDING
    elif ps == PAYMENT_COMPLETED:
        if not ds:
            row["deposit_status"] = DEPOSIT_STATUS_CONFIRMED
        if not rs:
            row["remaining_status"] = REMAINING_STATUS_CONFIRMED

    return row


def _migrate_raw(path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=BOOKING_COLUMNS)
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
    rows = []
    for _, r in raw.iterrows():
        rows.append(_backfill_payment_fields(r.to_dict()))
    return pd.DataFrame(rows, columns=BOOKING_COLUMNS) if rows else pd.DataFrame(columns=BOOKING_COLUMNS)


def load_bookings() -> pd.DataFrame:
    if BOOKINGS_FILE.exists():
        header = set(pd.read_csv(BOOKINGS_FILE, nrows=0).columns)
        needs = {"problem_description", "appointment_date", "province", "address"}
        missing_new = bool(_NEW_PAYMENT_COLS - header)
        if (
            not needs.issubset(header)
            or ("description" in header and "problem_description" not in header)
            or missing_new
        ):
            df = _migrate_raw(BOOKINGS_FILE)
            write_csv(BOOKINGS_FILE, df)
            return df
    return read_csv(BOOKINGS_FILE, BOOKING_COLUMNS)


def is_deposit_confirmed(booking: dict) -> bool:
    ps = str(booking.get("payment_status") or "")
    ds = str(booking.get("deposit_status") or "")
    if ps in (
        PAYMENT_CONFIRMED,
        PAYMENT_DEPOSIT_CONFIRMED,
        PAYMENT_REMAINING_PENDING,
        PAYMENT_COMPLETED,
    ):
        return True
    return ds == DEPOSIT_STATUS_CONFIRMED


def is_fully_paid(booking: dict) -> bool:
    ps = str(booking.get("payment_status") or "")
    if ps in (PAYMENT_CONFIRMED, PAYMENT_COMPLETED):
        return True
    return (
        str(booking.get("deposit_status") or "") == DEPOSIT_STATUS_CONFIRMED
        and str(booking.get("remaining_status") or "") == REMAINING_STATUS_CONFIRMED
    )


def can_access_tracking(booking: dict) -> bool:
    return is_deposit_confirmed(booking)


def can_pay_remaining(booking: dict) -> bool:
    if not is_deposit_confirmed(booking) or is_fully_paid(booking):
        return False
    status = normalize_service_status(booking)
    rs = str(booking.get("remaining_status") or "")
    if status in ("Servicio finalizado", "Saldo pendiente"):
        return True
    return rs == REMAINING_STATUS_PENDING


def normalize_service_status(booking: dict) -> str:
    """Mapea estados legacy al flujo de seguimiento con seña/saldo."""
    current = str(booking.get("service_status") or "").strip()
    legacy = {
        "Turno reservado": "Seña confirmada",
        "Pago confirmado": "Seña confirmada",
        "Reserva confirmada": "Seña confirmada",
    }
    if is_fully_paid(booking):
        if current in FINAL_SERVICE_STATUSES or current in ("Pago confirmado", "Seña confirmada", ""):
            # Reservas antiguas ya pagadas y finalizadas → Pago completado
            if (
                booking.get("booking_status") in FINAL_BOOKING_STATUSES
                or current in ("Servicio finalizado", "Completado", "Finalizado", "Pago completado")
            ):
                return "Pago completado"
            if current in legacy or current == "Seña confirmada":
                return "Seña confirmada"
        if current == "Pago completado":
            return current
    current = legacy.get(current, current)
    if current not in SERVICE_STATUS_FLOW:
        if is_deposit_confirmed(booking):
            return "Seña confirmada"
        return SERVICE_STATUS_FLOW[0]
    return current


def create_booking(**kwargs) -> dict:
    pro = get_professional(kwargs["professional_id"])
    if not pro:
        raise ValueError("Profesional no encontrado")

    df = load_bookings()
    booking_id = next_id(df, "BK")
    price = money_round(estimate_price(pro["base_price"], kwargs["urgency"]))
    total, deposit, remaining = split_deposit(price, DEPOSIT_PERCENTAGE)
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
        "initial_price": str(total),
        "approved_price": str(total),
        "estimated_arrival": kwargs.get("estimated_arrival", ""),
        "booking_status": BOOKING_TURNO_RESERVADO,
        "service_status": "Turno reservado",
        "payment_method": "",
        "payment_status": PAYMENT_DEPOSIT_PENDING,
        "payment_last_four": "",
        "card_brand": "",
        "payment_reference": "",
        "paid_at": "",
        "created_at": now,
        "confirmed_at": "",
        "completed_at": "",
        "guarantee_status": "Se activa al confirmar la seña",
        "warranty_until": "",
        "price_change_proposed": "",
        "price_change_reason": "",
        "terms_accepted": "True" if kwargs.get("terms_accepted") else "False",
        "work_completed": "",
        "chat_enabled": "False",
        "total_price": str(total),
        "deposit_percentage": str(DEPOSIT_PERCENTAGE),
        "deposit_amount": str(deposit),
        "deposit_status": DEPOSIT_STATUS_PENDING,
        "deposit_paid_at": "",
        "deposit_payment_method": "",
        "remaining_amount": str(remaining),
        "remaining_status": REMAINING_STATUS_BLOCKED,
        "remaining_paid_at": "",
        "remaining_payment_method": "",
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_csv(BOOKINGS_FILE, df)
    return row


def get_booking(booking_id: str) -> dict | None:
    df = load_bookings()
    match = df[df["id"] == booking_id]
    if match.empty:
        return None
    return _backfill_payment_fields(match.iloc[0].to_dict())


def update_booking(booking_id: str, **fields) -> dict | None:
    df = load_bookings()
    idx = df[df["id"] == booking_id].index
    if idx.empty:
        return None
    for key, val in fields.items():
        if key in BOOKING_COLUMNS:
            df.loc[idx, key] = str(val) if val is not None else ""
    write_csv(BOOKINGS_FILE, df)
    return _backfill_payment_fields(df.loc[idx[0]].to_dict())


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
    cancelled = booking_status.isin(CANCELLED_STATUSES)
    finalized = booking_status.isin(FINAL_BOOKING_STATUSES) | service_status.isin(
        {"Servicio finalizado", "Completado", "Finalizado", "Pago completado"}
    )
    # En curso: seña confirmada y aún no finalizado
    deposit_ok = source.apply(lambda r: is_deposit_confirmed(r.to_dict()), axis=1)
    in_progress = ~cancelled & ~finalized & deposit_ok
    upcoming = ~cancelled & ~finalized & ~in_progress

    return {
        "en_curso": source[in_progress].reset_index(drop=True),
        "proximos": source[upcoming].reset_index(drop=True),
        "finalizados": source[finalized].reset_index(drop=True),
    }


def flow_step_for_booking(booking: dict) -> int:
    """Paso de Servicios apropiado al reingresar desde Mi hogar."""
    status = normalize_service_status(booking)
    if is_fully_paid(booking) and status == "Pago completado":
        return 6
    if (
        booking.get("booking_status") in FINAL_BOOKING_STATUSES
        and is_fully_paid(booking)
    ):
        return 6
    if can_pay_remaining(booking):
        return 5
    if is_deposit_confirmed(booking):
        return 5
    return 3


def advance_service_status(booking_id: str) -> dict | None:
    from services.chat import add_professional_message, add_system_message, pro_message_for_status

    booking = get_booking(booking_id)
    if not booking:
        return None
    if not is_deposit_confirmed(booking):
        return booking
    flow = SERVICE_STATUS_FLOW
    current = normalize_service_status(booking)
    if current not in flow:
        current = flow[0]
    idx = flow.index(current)
    # No avanzar automáticamente de Servicio finalizado → Saldo pendiente vía demo
    # si ya está en Saldo pendiente; desde Servicio finalizado sí pasa a Saldo pendiente.
    if idx >= len(flow) - 1:
        return booking
    # Bloquear avance a Pago completado sin pagar saldo
    if flow[idx + 1] == "Pago completado":
        return booking
    nxt = flow[idx + 1]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    fields: dict = {"service_status": nxt}
    if nxt == "Seña confirmada":
        fields["booking_status"] = BOOKING_RESERVA_CONFIRMADA
    elif nxt in ("Profesional en camino", "Profesional en el domicilio", "Trabajo en curso"):
        fields["booking_status"] = BOOKING_EN_SEGUIMIENTO
    elif nxt == "Servicio finalizado":
        fields["completed_at"] = now
        fields["warranty_until"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    elif nxt == "Saldo pendiente":
        fields["remaining_status"] = REMAINING_STATUS_PENDING
        fields["payment_status"] = PAYMENT_REMAINING_PENDING
        fields["booking_status"] = BOOKING_FINALIZADA
    result = update_booking(booking_id, **fields)
    if nxt in SYSTEM_STATUS_KEYS:
        add_system_message(booking_id, nxt)
    pro_msg = pro_message_for_status(nxt, booking.get("professional_name", "Profesional"))
    if pro_msg:
        add_professional_message(booking_id, booking.get("professional_name", "Profesional"), pro_msg)
    return result


SYSTEM_STATUS_KEYS = {
    "Seña confirmada",
    "Pago confirmado",
    "Profesional en camino",
    "Profesional en el domicilio",
    "Servicio finalizado",
    "Saldo pendiente",
    "Pago completado",
}


def propose_price_change(booking_id: str, new_price: float, reason: str) -> dict | None:
    return update_booking(
        booking_id,
        price_change_proposed=str(money_round(new_price)),
        price_change_reason=reason,
    )


def accept_price_change(booking_id: str) -> dict | None:
    """Acepta nuevo precio: no recalcula la seña; solo actualiza total y saldo."""
    booking = get_booking(booking_id)
    if not booking or not booking.get("price_change_proposed"):
        return booking
    new_total = money_round(booking["price_change_proposed"])
    totals = booking_totals(booking)
    deposit = totals["deposit"]
    remaining = new_total - deposit
    if remaining < 0:
        remaining = money_round(0)
    fields = {
        "approved_price": str(new_total),
        "total_price": str(new_total),
        "remaining_amount": str(remaining),
        "price_change_proposed": "",
        "price_change_reason": "",
    }
    # Si la seña ya está paga y el trabajo terminó, el saldo queda pendiente
    if is_deposit_confirmed(booking) and not is_fully_paid(booking):
        status = normalize_service_status(booking)
        if status in ("Servicio finalizado", "Saldo pendiente"):
            fields["remaining_status"] = REMAINING_STATUS_PENDING
            fields["payment_status"] = PAYMENT_REMAINING_PENDING
    return update_booking(booking_id, **fields)


def appointment_label(booking: dict) -> str:
    return format_appointment(
        booking.get("appointment_date") or booking.get("preferred_date", ""),
        booking.get("appointment_time") or booking.get("preferred_time", ""),
    )
