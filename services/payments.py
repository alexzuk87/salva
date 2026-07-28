"""Pagos simulados (prototipo académico) — seña 20% y saldo 80%."""

import re
from datetime import datetime

from services.bookings import (
    BOOKING_RESERVA_CONFIRMADA,
    DEPOSIT_STATUS_CONFIRMED,
    PAYMENT_COMPLETED,
    PAYMENT_DEPOSIT_CONFIRMED,
    PAYMENT_REMAINING_PENDING,
    REMAINING_STATUS_BLOCKED,
    REMAINING_STATUS_CONFIRMED,
    REMAINING_STATUS_PENDING,
    get_booking,
    is_deposit_confirmed,
    update_booking,
)

PAYMENT_METHODS = ["Tarjeta de crédito", "Transferencia bancaria / alias", "SALVA Cuenta"]


def detect_card_brand(number: str) -> str:
    """Detecta marca solo para UI; no condiciona la validación del prototipo."""
    digits = re.sub(r"\D", "", number)
    if not digits:
        return ""
    if digits.startswith("4"):
        return "Visa"
    if len(digits) >= 2:
        prefix2 = int(digits[:2])
        if 51 <= prefix2 <= 55:
            return "Mastercard"
        if len(digits) >= 4:
            prefix4 = int(digits[:4])
            if 2221 <= prefix4 <= 2720:
                return "Mastercard"
    return ""


def format_card_number(number: str) -> str:
    digits = re.sub(r"\D", "", number)[:16]
    parts = [digits[i:i + 4] for i in range(0, len(digits), 4)]
    return " ".join(parts)


def sanitize_card_input(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)[:16]
    return format_card_number(digits)


def sanitize_month(raw: str) -> str:
    return re.sub(r"\D", "", raw)[:2]


def sanitize_year(raw: str) -> str:
    return re.sub(r"\D", "", raw)[:2]


def sanitize_cvv(raw: str) -> str:
    return re.sub(r"\D", "", raw)[:3]


def validate_card(number: str, holder: str, month: str, year: str, cvv: str) -> tuple[bool, str, str]:
    digits = re.sub(r"\D", "", number)
    brand = detect_card_brand(digits)
    if len(digits) != 16:
        return False, "Ingresá los 16 números de la tarjeta.", brand
    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ'\s]{2,}", holder.strip()):
        return False, "Ingresá el nombre del titular.", brand
    mm_s, yy_s = sanitize_month(month), sanitize_year(year)
    if len(mm_s) != 2 or len(yy_s) != 2:
        return False, "Completá mes y año con 2 dígitos.", brand
    mm, yy = int(mm_s), int(yy_s)
    if mm < 1 or mm > 12:
        return False, "El mes de vencimiento no es válido.", brand
    now = datetime.now()
    exp_date = datetime(2000 + yy, mm, 1)
    if exp_date < datetime(now.year, now.month, 1):
        return False, "La fecha de vencimiento ya pasó.", brand
    if len(sanitize_cvv(cvv)) != 3:
        return False, "El código de seguridad debe tener 3 números.", brand
    return True, "", brand or "Tarjeta"


def _payment_ref(booking_id: str, kind: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    stamp = now.replace(":", "").replace("-", "").replace(" ", "")[-6:]
    return f"TXN-{kind}-{booking_id}-{stamp}"


def confirm_deposit(
    booking_id: str,
    payment_method: str,
    last_four: str = "",
    card_brand: str = "",
) -> dict | None:
    """Confirma únicamente la seña (20%). Habilita chat y seguimiento."""
    booking = get_booking(booking_id)
    if not booking:
        return None
    if is_deposit_confirmed(booking):
        return booking
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ref = _payment_ref(booking_id, "SEN")
    return update_booking(
        booking_id,
        payment_method=payment_method,
        payment_status=PAYMENT_DEPOSIT_CONFIRMED,
        payment_last_four=last_four,
        card_brand=card_brand,
        payment_reference=ref,
        paid_at=now,
        confirmed_at=now,
        booking_status=BOOKING_RESERVA_CONFIRMADA,
        service_status="Seña confirmada",
        guarantee_status="Cobertura activa",
        chat_enabled="True",
        deposit_status=DEPOSIT_STATUS_CONFIRMED,
        deposit_paid_at=now,
        deposit_payment_method=payment_method,
        remaining_status=REMAINING_STATUS_BLOCKED,
    )


def confirm_remaining(
    booking_id: str,
    payment_method: str,
    last_four: str = "",
    card_brand: str = "",
) -> dict | None:
    """Confirma el saldo (80%) tras finalizar el trabajo."""
    from services.bookings import can_pay_remaining

    booking = get_booking(booking_id)
    if not booking:
        return None
    if not is_deposit_confirmed(booking):
        return booking
    if not can_pay_remaining(booking):
        return booking
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ref = _payment_ref(booking_id, "SAL")
    return update_booking(
        booking_id,
        payment_method=payment_method,
        payment_status=PAYMENT_COMPLETED,
        payment_last_four=last_four or booking.get("payment_last_four", ""),
        card_brand=card_brand or booking.get("card_brand", ""),
        payment_reference=ref,
        paid_at=now,
        booking_status="Servicio finalizado",
        service_status="Pago completado",
        remaining_status=REMAINING_STATUS_CONFIRMED,
        remaining_paid_at=now,
        remaining_payment_method=payment_method,
        work_completed=booking.get("work_completed")
        or booking.get("problem_description")
        or booking.get("service_type")
        or "Servicio completado",
    )


def confirm_payment(
    booking_id: str,
    payment_method: str,
    last_four: str = "",
    card_brand: str = "",
) -> dict | None:
    """Compatibilidad: si falta la seña, confirma seña; si el saldo está pendiente, confirma saldo."""
    booking = get_booking(booking_id)
    if not booking:
        return None
    if not is_deposit_confirmed(booking):
        return confirm_deposit(booking_id, payment_method, last_four, card_brand)
    rs = str(booking.get("remaining_status") or "")
    ps = str(booking.get("payment_status") or "")
    if rs == REMAINING_STATUS_PENDING or ps == PAYMENT_REMAINING_PENDING:
        return confirm_remaining(booking_id, payment_method, last_four, card_brand)
    return booking
