"""Pagos simulados (prototipo académico) — Visa y Mastercard únicamente."""

import re
from datetime import datetime

from services.bookings import PAYMENT_CONFIRMED, get_booking, update_booking

PAYMENT_METHODS = ["Tarjeta de crédito", "Transferencia bancaria / alias", "SALVA Cuenta"]


def detect_card_brand(number: str) -> str:
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
    if brand not in ("Visa", "Mastercard"):
        return False, "Ingresá una tarjeta Visa o Mastercard válida para esta simulación.", brand
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
    return True, "", brand


def confirm_payment(
    booking_id: str,
    payment_method: str,
    last_four: str = "",
    card_brand: str = "",
) -> dict | None:
    booking = get_booking(booking_id)
    if not booking:
        return None
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ref = f"TXN-{booking_id}-{now.replace(':', '').replace('-', '').replace(' ', '')[-6:]}"
    return update_booking(
        booking_id,
        payment_method=payment_method,
        payment_status=PAYMENT_CONFIRMED,
        payment_last_four=last_four,
        card_brand=card_brand,
        payment_reference=ref,
        paid_at=now,
        confirmed_at=now,
        booking_status="Reserva confirmada",
        service_status="Pago confirmado",
        guarantee_status="Cobertura activa",
        chat_enabled="True",
    )
