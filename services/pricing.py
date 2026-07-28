"""Cálculos de precio, seña (20%) y saldo (80%)."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

DEPOSIT_PERCENTAGE = 20


def _to_decimal(amount: float | int | str | Decimal) -> Decimal:
    if isinstance(amount, Decimal):
        return amount
    return Decimal(str(amount or 0))


def money_round(amount: float | int | str | Decimal) -> Decimal:
    """Redondeo monetario a entero (ARS sin centavos en el prototipo)."""
    return _to_decimal(amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def split_deposit(
    total_price: float | int | str | Decimal,
    percentage: int = DEPOSIT_PERCENTAGE,
) -> tuple[Decimal, Decimal, Decimal]:
    """Devuelve (total, seña, saldo) con enteros consistentes.

    La seña es percentage% del total; el saldo es el resto (evita drift de redondeo).
    """
    total = money_round(total_price)
    pct = Decimal(int(percentage))
    deposit = money_round(total * pct / Decimal(100))
    remaining = total - deposit
    return total, deposit, remaining


def prices_from_professionals(prices: list[float | int | str]) -> tuple[float | None, float | None]:
    """Min/max a partir de precios reales de profesionales visibles."""
    values: list[float] = []
    for p in prices:
        try:
            values.append(float(p))
        except (TypeError, ValueError):
            continue
    if not values:
        return None, None
    return min(values), max(values)


def booking_totals(booking: dict[str, Any]) -> dict[str, Decimal]:
    """Lee total/seña/saldo de la reserva, recalculando saldo si hace falta."""
    total_raw = booking.get("total_price") or booking.get("approved_price") or booking.get("initial_price") or 0
    total = money_round(total_raw)
    pct = int(float(booking.get("deposit_percentage") or DEPOSIT_PERCENTAGE) or DEPOSIT_PERCENTAGE)
    if booking.get("deposit_amount") not in (None, ""):
        deposit = money_round(booking["deposit_amount"])
    else:
        _, deposit, _ = split_deposit(total, pct)
    if booking.get("remaining_amount") not in (None, ""):
        remaining = money_round(booking["remaining_amount"])
    else:
        remaining = total - deposit
    return {
        "total": total,
        "deposit": deposit,
        "remaining": remaining,
        "percentage": Decimal(pct),
    }
