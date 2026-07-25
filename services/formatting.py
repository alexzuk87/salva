"""Formato de moneda argentina."""


def format_ars(amount: float | int | str) -> str:
    value = float(amount)
    if value == int(value):
        return f"${f'{int(value):,}'.replace(',', '.')}"
    whole, decimals = f"{value:.2f}".split(".")
    return f"${f'{int(whole):,}'.replace(',', '.')},{decimals}"
