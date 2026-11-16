"""Predicción de demanda (iteración 68): regresión lineal sobre lo pedido en las semanas anteriores, por zona."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import ROUND_CEILING, Decimal

from . import cycle as cycles
from .store import InMemoryStore

WEEKS = 8  # S-339
MIN_FOR_TREND = 3  # S-340
ZERO = Decimal("0")


def weekly_demand(store: InMemoryStore, cycle: str) -> dict[tuple[str, str], Decimal]:
    """S-341 y S-343: lo pedido en la semana (sin cancelados) más la historia importada, por (zona, producto)."""
    demand: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    for order in store.orders_in_cycle(cycle):
        if order.status == "CANCELADO_POR_CLIENTE":
            continue
        for line in order.lines:
            demand[(order.zone_id, line.product_id)] += line.quantity
    for (week, zone_id, product_id), quantity in store.demand_history.items():
        if week == cycle:
            demand[(zone_id, product_id)] += quantity
    return demand


def predict(series: list[Decimal]) -> tuple[Decimal, str]:
    """S-340: recta por mínimos cuadrados leída en la semana siguiente; promedio si hay pocas semanas."""
    n = len(series)
    if not n:
        return ZERO, "sin_historia"
    if n < MIN_FOR_TREND:
        return max(ZERO, sum(series, ZERO) / n), "promedio"
    mean_x = Decimal(n - 1) / 2
    mean_y = sum(series, ZERO) / n
    slope = (sum((Decimal(x) - mean_x) * (y - mean_y) for x, y in enumerate(series))
             / sum((Decimal(x) - mean_x) ** 2 for x in range(n)))
    return max(ZERO, mean_y + slope * (n - mean_x)), "tendencia"


def _round_up(quantity: Decimal, step: Decimal) -> Decimal:
    """S-342."""
    if quantity <= 0:
        return ZERO
    steps = (quantity / step).quantize(Decimal("1e-9")).to_integral_value(ROUND_CEILING)
    return steps * step


def forecast(store: InMemoryStore, cycle: str, now: datetime) -> dict:
    """PD-01..PD-04."""
    weeks = [cycles.add_weeks(cycle, -back) for back in range(WEEKS, 0, -1)]
    history = [weekly_demand(store, week) for week in weeks]
    catalog = {p.product_id: p for p in store.catalog_for(cycle).values() if p.active}
    zones_first = {}  # S-339: la serie de una zona empieza en la primera semana en que pidió
    for i, demand in enumerate(history):
        for zone_id, _ in demand:
            zones_first.setdefault(zone_id, i)

    per_zone: dict[str, dict[str, Decimal]] = defaultdict(dict)
    methods: dict[str, str] = {}
    for zone_id, first in zones_first.items():
        for product_id in catalog:
            series = [demand.get((zone_id, product_id), ZERO) for demand in history[first:]]
            if not any(series):
                continue
            estimate, method = predict(series)
            per_zone[zone_id][product_id] = estimate
            if methods.get(product_id) != "tendencia":
                methods[product_id] = method

    ordered = weekly_demand(store, cycle)
    closed = cycles.to_lima(now) >= cycles.closes_at(cycle)
    products, errors = [], []
    for product_id, product in catalog.items():
        estimate = _round_up(sum((z.get(product_id, ZERO) for z in per_zone.values()), ZERO), product.step)
        asked = sum((q for (_, p), q in ordered.items() if p == product_id), ZERO)
        if closed and asked > 0:
            errors.append(abs(estimate - asked) / asked)
        products.append({"id": product_id, "nombre": product.name, "unidad": product.unit,
                         "historia": [sum((q for (_, p), q in d.items() if p == product_id), ZERO) for d in history],
                         "estimado": estimate, "pedido": asked, "maximo": product.max_available,
                         "supera_maximo": estimate > product.max_available,
                         "metodo": methods.get(product_id, "sin_historia")})
    zones = [{"id": zone_id, "nombre": store.zones[zone_id].name if zone_id in store.zones else zone_id,
              "productos": [{"id": p, "estimado": _round_up(q, catalog[p].step)} for p, q in estimates.items() if q > 0]}
             for zone_id, estimates in per_zone.items()]
    mean_error = (sum(errors, ZERO) / len(errors)).quantize(Decimal("0.01")) if errors else None
    return {"ciclo": cycle, "semanas": weeks, "productos": products, "zonas": zones, "error_medio": mean_error}
