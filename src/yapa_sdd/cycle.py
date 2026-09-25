"""Ciclo semanal en hora de Lima (RP-03, S-02)."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone


# Lima no usa horario de verano: UTC-5 todo el año.
LIMA = timezone(timedelta(hours=-5), "America/Lima")
CLOSE_TIME = time(20, 0)


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
