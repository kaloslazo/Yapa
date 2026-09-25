"""Ciclo semanal en hora de Lima (RP-03, S-02)."""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta, timezone


# Lima no usa horario de verano: UTC-5 todo el año.
LIMA = timezone(timedelta(hours=-5), "America/Lima")
CLOSE_TIME = time(20, 0)


def check_cycle_id(cycle: str) -> None:
    """HR-06: identificador AAAA-Wnn de una semana que existe."""
    from .domain import BusinessRuleError

    match = re.fullmatch(r"(\d{4})-W(\d{2})", cycle or "")
    try:
        if not match:
            raise ValueError
        datetime.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)
    except ValueError:
        raise BusinessRuleError("INVALID_CYCLE", f"El ciclo '{cycle}' no es válido.")


def to_lima(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ValueError("La fecha debe indicar zona horaria.")
    return moment.astimezone(LIMA)


def cycle_id(moment: datetime) -> str:
    year, week, _ = to_lima(moment).isocalendar()
    return f"{year}-W{week:02d}"


def is_open(moment: datetime) -> bool:
    """Abierto desde el lunes 00:00 hasta antes del miércoles 20:00."""
    local = to_lima(moment)
    weekday = local.weekday()  # lunes = 0
    if weekday in (0, 1):
        return True
    return weekday == 2 and local.time() < CLOSE_TIME


def opens_at(cycle: str) -> datetime:
    """Lunes 00:00 (hora de Lima) de la semana del ciclo, por ejemplo "2026-W39"."""
    year, week = cycle.split("-W")
    monday = datetime.fromisocalendar(int(year), int(week), 1)
    return datetime.combine(monday.date(), time(0, 0), LIMA)


def closes_at(cycle: str) -> datetime:
    """Miércoles 20:00 (hora de Lima) del ciclo: desde ahí ya no entran pedidos."""
    return opens_at(cycle) + timedelta(days=2, hours=CLOSE_TIME.hour)


def add_weeks(cycle: str, weeks: int) -> str:
    """El ciclo que viene `weeks` semanas después, por ejemplo W38 + 3 = W41."""
    return cycle_id(opens_at(cycle) + timedelta(weeks=weeks))
