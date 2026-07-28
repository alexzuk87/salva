"""Agenda con franjas de 30 minutos."""

from datetime import date, datetime, timedelta

URGENCY_LEVELS = ["Emergencia", "Hoy", "Programado"]

ASAP = "ASAP"
ASAP_LABEL = "Lo antes posible"

MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
WEEKDAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def all_half_hour_slots() -> list[str]:
    slots = []
    for h in range(8, 20):
        slots.append(f"{h:02d}:00")
        slots.append(f"{h:02d}:30")
    return slots


def is_asap(slot: str) -> bool:
    return str(slot or "").strip() in (ASAP, ASAP_LABEL)


def slot_display(slot: str) -> str:
    if is_asap(slot):
        return ASAP_LABEL
    return str(slot or "")


def slot_period(slot: str) -> str:
    """Clasifica un slot. ASAP y valores inválidos no se parsean como hora."""
    if is_asap(slot):
        return "Urgente"
    if not slot or ":" not in str(slot):
        return "Otro"
    try:
        hour = int(str(slot).split(":")[0])
    except (ValueError, IndexError):
        return "Otro"
    if hour < 12:
        return "Mañana"
    if hour < 17:
        return "Tarde"
    return "Noche"


def grouped_slots(slots: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {"Urgente": [], "Mañana": [], "Tarde": [], "Noche": []}
    for s in slots:
        period = slot_period(s)
        if period not in groups:
            groups[period] = []
        groups[period].append(s)
    return groups


def available_slots(urgency: str, appointment_date: date, pro_availability: str = "") -> list[str]:
    today = date.today()
    if appointment_date < today:
        return []
    all_slots = all_half_hour_slots()
    if urgency == "Emergencia":
        now = datetime.now()
        if appointment_date == today:
            emergency = [ASAP]
            for s in all_slots:
                h, m = map(int, s.split(":"))
                slot_dt = datetime.combine(today, datetime.min.time().replace(hour=h, minute=m))
                if slot_dt >= now + timedelta(minutes=30):
                    emergency.append(s)
                    if len(emergency) >= 5:
                        break
            return emergency
        return [ASAP] + all_slots[:4]
    if urgency == "Hoy" and appointment_date == today:
        now = datetime.now()
        return [
            s for s in all_slots
            if datetime.combine(today, datetime.min.time().replace(
                hour=int(s.split(":")[0]), minute=int(s.split(":")[1])
            )) >= now + timedelta(minutes=30)
        ]
    avail_parts = [x.strip() for x in str(pro_availability).split(",") if x.strip()]
    if not avail_parts or "Flexible" in avail_parts:
        return all_slots
    result = []
    for s in all_slots:
        period = slot_period(s)
        if period in avail_parts or any(p in avail_parts for p in (s, period)):
            result.append(s)
    return result or all_slots


def format_appointment(appointment_date: str, appointment_time: str) -> str:
    if not appointment_date:
        return "—"
    try:
        d = datetime.strptime(appointment_date[:10], "%Y-%m-%d").date()
    except ValueError:
        return f"{appointment_date} · {slot_display(appointment_time) or '—'}"
    wd = WEEKDAYS_ES[d.weekday()]
    month = MONTHS_ES[d.month - 1]
    label = f"{wd} {d.day} de {month}"
    if appointment_time:
        if is_asap(appointment_time):
            return f"{label} · {ASAP_LABEL}"
        return f"{label} · {appointment_time} h"
    return label


def format_selected_turno(appointment_date: date | str, appointment_time: str) -> str:
    """Confirmación compacta del turno (día en minúscula)."""
    if isinstance(appointment_date, date):
        date_str = appointment_date.isoformat()
    else:
        date_str = str(appointment_date or "")
    base = format_appointment(date_str, appointment_time)
    if not base or base == "—":
        return ""
    parts = base.split(" ", 1)
    parts[0] = parts[0].lower()
    return f"Turno seleccionado: {' '.join(parts)}"


def min_appointment_date(urgency: str) -> date:
    today = date.today()
    if urgency in ("Emergencia", "Hoy"):
        return today
    return today + timedelta(days=1)


def _run_slot_period_tests() -> None:
    assert slot_period("08:00") == "Mañana"
    assert slot_period("13:30") == "Tarde"
    assert slot_period("19:00") == "Noche"
    assert slot_period(ASAP) == "Urgente"
    assert slot_period(ASAP_LABEL) == "Urgente"
    assert slot_period("") == "Otro"
    assert slot_period("invalid") == "Otro"
    print("SCHEDULING_TESTS_OK")


if __name__ == "__main__":
    _run_slot_period_tests()
