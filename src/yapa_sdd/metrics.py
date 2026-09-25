"""Métricas del piloto: margen por pedido, ahorro entregado y recompra en la semana 4 (iteración 8).

Spec: docs/desarrollo/08-metricas-piloto.md. Solo lee datos; no cambia nada del ciclo.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from . import cycle as cycles
from .domain import BusinessRuleError
from .settlement import CycleSettlement, SettledOrder
from .store import InMemoryStore


ZERO = Decimal("0")
REPURCHASE_TARGET = Decimal("50")  # S-48, en %


@dataclass(frozen=True)
class OrderMargin:
    order_id: int
    revenue: Decimal
    claims: Decimal
    product_cost: Decimal
    stop_cost: Decimal
    margin: Decimal


@dataclass(frozen=True)
class Savings:
    volume: Decimal
    delivery: Decimal
    total: Decimal


@dataclass(frozen=True)
class Repurchase:
    cohort_cycle: str
    target_cycle: str
    cohort_size: int
    returned: int
    rate: Decimal
    meets_target: bool


def _settlement(store: InMemoryStore, cycle: str) -> CycleSettlement:
    result = store.settlements.get(cycle)
    if result is None:  # MT-01, S-52
        raise BusinessRuleError("CYCLE_NOT_SETTLED", f"El ciclo {cycle} todavía no se liquidó.")
    return result


def _liquidated(result: CycleSettlement) -> list[SettledOrder]:
    """S-47: solo cuentan los pedidos liquidados."""
    return [order for order in result.orders.values() if order.status == "LIQUIDADO"]


def order_margins(store: InMemoryStore, cycle: str) -> dict[int, OrderMargin]:
    """MT-02, S-49: margen de contribución de cada pedido liquidado."""
    result = _settlement(store, cycle)
    liquidated = _liquidated(result)
    orders_per_zone = Counter(store.orders[settled.order_id].zone_id for settled in liquidated)
    catalog = store.catalog_for(cycle)
    margins = {}
    for settled in liquidated:
        order = store.orders[settled.order_id]
        product_cost = ZERO
        for line in settled.lines:
            total_quantity = result.products[line.product_id].total_quantity
            product_cost += catalog[line.product_id].tier_for(total_quantity).base_price * line.delivered
        stop_cost = store.zones[order.zone_id].stop_cost / orders_per_zone[order.zone_id]
        claims = sum((claim.refund_amount for claim in store.claims.values()
                      if claim.order_id == order.order_id and claim.status == "APROBADO"), ZERO)
        margin = settled.final_amount - claims - product_cost - stop_cost
        margins[order.order_id] = OrderMargin(order.order_id, settled.final_amount, claims, product_cost,
                                              stop_cost, margin)
    return margins


def margin_alerts(store: InMemoryStore, cycle: str) -> list[int]:
    """MT-03, S-50: pedidos con margen negativo."""
    return [order_id for order_id, margin in sorted(order_margins(store, cycle).items()) if margin.margin < 0]


def delivered_savings(store: InMemoryStore, cycle: str) -> Savings:
    """MT-04, S-51: ahorro por volumen y por envío compartido, sin faltantes ni reclamos."""
    result = _settlement(store, cycle)
    volume = ZERO
    delivery = ZERO
    for settled in _liquidated(result):
        order = store.orders[settled.order_id]
        max_prices = {line.product_id: line.max_unit_price for line in order.lines}
        for line in settled.lines:
            volume += (max_prices[line.product_id] - line.final_unit_price) * line.delivered
        delivery += order.delivery_fee - settled.delivery_fee
    return Savings(volume, delivery, volume + delivery)


def repurchase_week4(store: InMemoryStore, cohort_cycle: str) -> Repurchase:
    """MT-05, S-48: de los que compraron por primera vez en N, cuántos compran en N + 3."""
    target_cycle = cycles.add_weeks(cohort_cycle, 3)
    _settlement(store, cohort_cycle)
    _settlement(store, target_cycle)
    purchases: dict[int, set[str]] = {}
    for order in store.orders.values():
        if order.status == "LIQUIDADO":  # S-47
            purchases.setdefault(order.customer_id, set()).add(order.cycle)
    cohort = [customer for customer, bought in purchases.items() if min(bought) == cohort_cycle]
    if not cohort:
        raise BusinessRuleError("EMPTY_COHORT", f"Nadie compró por primera vez en {cohort_cycle}.")
    returned = sum(1 for customer in cohort if target_cycle in purchases[customer])
    rate = Decimal(returned) * 100 / len(cohort)
    return Repurchase(cohort_cycle, target_cycle, len(cohort), returned, rate, rate >= REPURCHASE_TARGET)


# --- Iteración 13: margen neto con costos operativos (docs/desarrollo/13-margen-neto.md) ---


@dataclass(frozen=True)
class OperatingCosts:
    """S-95: costos por pedido que no están en el margen de contribución."""

    name: str
    purchase_trip: Decimal
    packing: Decimal
    support: Decimal
    payment_fee_rate: Decimal  # sobre lo pagado por Yape/Plin


OPTIMISTIC = OperatingCosts("OPTIMISTA", Decimal("0"), Decimal("1.60"), Decimal("0.73"), Decimal("0"))  # S-96
PESSIMISTIC = OperatingCosts("PESIMISTA", Decimal("3.33"), Decimal("1.60"), Decimal("0.73"), Decimal("0.0295"))  # S-97


@dataclass(frozen=True)
class NetMargin:
    order_id: int
    contribution: Decimal
    payment_fee: Decimal
    operating_cost: Decimal
    net_margin: Decimal


@dataclass(frozen=True)
class NetMarginSummary:
    scenario: str
    orders: int
    average_net_margin: Decimal
    losing_orders: int
    shortfall_per_losing_order: Decimal


def net_margins(store: InMemoryStore, cycle: str, costs: OperatingCosts) -> dict[int, NetMargin]:
    """NM-01 y NM-02: margen de contribución menos costos operativos del escenario."""
    result = {}
    for order_id, margin in order_margins(store, cycle).items():
        fee = store.orders[order_id].paid_external * costs.payment_fee_rate
        operating = costs.purchase_trip + costs.packing + costs.support + fee
        result[order_id] = NetMargin(order_id, margin.margin, fee, operating, margin.margin - operating)
    return result


def net_margin_summary(store: InMemoryStore, cycle: str, costs: OperatingCosts) -> NetMarginSummary:
    """NM-03: cuánto deja en promedio y cuánto falta en los pedidos que pierden."""
    margins = list(net_margins(store, cycle, costs).values())
    losing = [m for m in margins if m.net_margin < 0]
    average = sum((m.net_margin for m in margins), ZERO) / len(margins) if margins else ZERO
    shortfall = -sum((m.net_margin for m in losing), ZERO) / len(losing) if losing else ZERO
    return NetMarginSummary(costs.name, len(margins), average, len(losing), shortfall)
