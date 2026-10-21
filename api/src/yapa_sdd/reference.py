"""Precio de referencia del mercado y del supermercado (iteración 22).

Spec: docs/desarrollo/22-precio-referencia.md (S-125..S-129).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from . import cycle as cycles
from .domain import BusinessRuleError
from .store import InMemoryStore


KINDS = ("MERCADO", "SUPERMERCADO")
VALID_DAYS = 14  # S-126
TARGET_SAVINGS = Decimal("15")  # S-128, el mismo % del kit de campo
ZERO = Decimal("0")


@dataclass(frozen=True)
class ReferencePrice:
    product_id: str
    kind: str
    price: Decimal
    source: str
    observed_on: date
    by: str
    registered_at: datetime


@dataclass(frozen=True)
class ReferenceSavings:
    baskets: int
    reference_total: Decimal
    yapa_total: Decimal
    savings: Decimal
    percent: Decimal | None


def register_reference(store: InMemoryStore, product_id: str, kind: str, price: Decimal, source: str,
                       observed_on: date, *, by: str, now: datetime) -> ReferencePrice:
    if by not in store.admins:  # RF-01
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo el administrador de Yapa registra precios de referencia.")
    if product_id not in store.products and product_id not in store.catalog_for(cycles.cycle_id(now)):  # RF-02
        raise BusinessRuleError("PRODUCT_NOT_AVAILABLE", f"{product_id} no está en el catálogo.")
    if kind not in KINDS:  # RF-03
        raise BusinessRuleError("INVALID_REFERENCE_KIND", "El tipo es mercado de barrio o supermercado.")
    if price <= 0:  # RF-04
        raise BusinessRuleError("INVALID_PRICE", "El precio tiene que ser mayor que 0.")
    source = (source or "").strip()
    if not source:
        raise BusinessRuleError("SOURCE_REQUIRED", "Indica dónde se vio el precio.")
    if observed_on > cycles.to_lima(now).date():
        raise BusinessRuleError("INVALID_DATE", "La fecha no puede ser futura.")
    reference = ReferencePrice(product_id, kind, price, source, observed_on, by, now)
    store.reference_prices.append(reference)
    return reference


def _is_current(reference: ReferencePrice, day: date) -> bool:
    return abs((day - reference.observed_on).days) <= VALID_DAYS


def current_references(store: InMemoryStore, product_id: str, day: date) -> dict[str, ReferencePrice]:
    """RF-05: el más reciente por fecha, si sigue vigente (S-126)."""
    found: dict[str, ReferencePrice] = {}
    for reference in store.reference_prices:  # en orden de registro: con la misma fecha gana el último
        if reference.product_id != product_id or reference.observed_on > day:
            continue
        previous = found.get(reference.kind)
        if previous is None or reference.observed_on >= previous.observed_on:
            found[reference.kind] = reference
    return {kind: ref for kind, ref in found.items() if _is_current(ref, day)}


def _near_close(store: InMemoryStore, product_id: str, kind: str, day: date) -> ReferencePrice | None:
    """S-129: el precio de ese tipo más cercano al cierre, a 14 días o menos, antes o después.
    Con la misma distancia gana el de fecha más nueva y, con la misma fecha, el último registrado."""
    best, best_key = None, None
    for reference in store.reference_prices:
        if reference.product_id != product_id or reference.kind != kind or not _is_current(reference, day):
            continue
        key = (abs((day - reference.observed_on).days), -reference.observed_on.toordinal())
        if best_key is None or key <= best_key:
            best, best_key = reference, key
    return best


def _basket_reference(store: InMemoryStore, settled, kind: str, day: date) -> Decimal | None:
    """S-129: lo que costaba allá lo recibido; None si algún producto no tiene precio de ese tipo."""
    lines = [line for line in settled.lines if line.delivered > 0]
    references = [_near_close(store, line.product_id, kind, day) for line in lines]
    if settled.status != "LIQUIDADO" or not lines or None in references:
        return None
    return sum((ref.price * line.delivered for ref, line in zip(references, lines)), ZERO)


@dataclass(frozen=True)
class OrderComparison:
    reference_total: Decimal
    savings: Decimal


def order_comparison(store: InMemoryStore, order_id: int) -> dict[str, OrderComparison]:
    """MA-01: por tipo, solo si el pedido está liquidado y su canasta es comparable."""
    order = store.orders[order_id]
    result = store.settlements.get(order.cycle)
    settled = result.orders.get(order_id) if result else None
    if settled is None:
        return {}
    day = cycles.closes_at(order.cycle).date()
    comparison = {}
    for kind in KINDS:
        total = _basket_reference(store, settled, kind, day)
        if total is not None:
            comparison[kind] = OrderComparison(total, total - settled.final_amount)
    return comparison


def savings_percent(yapa_price: Decimal, reference_price: Decimal) -> Decimal:
    return (1 - yapa_price / reference_price) * 100


def reference_savings(store: InMemoryStore, cycle: str) -> dict[str, ReferenceSavings]:
    """RF-08: ahorro real frente a cada tipo de referencia, solo con canastas comparables."""
    result = store.settlements.get(cycle)
    if result is None:
        raise BusinessRuleError("CYCLE_NOT_SETTLED", f"El ciclo {cycle} todavía no se liquidó.")
    close_day = cycles.closes_at(cycle).date()
    summary = {}
    for kind in KINDS:
        baskets, reference_total, yapa_total = 0, ZERO, ZERO
        for settled in result.orders.values():
            total = _basket_reference(store, settled, kind, close_day)  # MA-04: la misma cuenta por canasta
            if total is None:
                continue
            baskets += 1
            reference_total += total
            yapa_total += settled.final_amount
        savings = reference_total - yapa_total
        percent = savings / reference_total * 100 if baskets else None
        summary[kind] = ReferenceSavings(baskets, reference_total, yapa_total, savings, percent)
    return summary
