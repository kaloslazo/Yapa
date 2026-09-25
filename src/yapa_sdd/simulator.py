"""Simulador de escenarios para decidir comisión y mínimo de zona (iteración 14).

Spec: docs/desarrollo/14-simulador-escenarios.md. Usa las mismas reglas del sistema sobre un
repositorio aparte; no toca datos reales.

Uso: PYTHONPATH=src python -m yapa_sdd.simulator [costo_parada]
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from . import domain
from .cycle import LIMA, cycle_id
from .domain import Customer, Zone
from .metrics import OPTIMISTIC, PESSIMISTIC, OperatingCosts, delivered_savings, net_margin_summary
from .order_registration import quote_order, register_order, verify_payment
from .seed import pilot_store
from .settlement import settle_cycle


BASKET = [("PAPA-AMARILLA", "5"), ("PAPA-BLANCA", "10"), ("CEBOLLA-ROJA", "10")]  # S-98
WHEN = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
MIN_ORDERS, MAX_ORDERS = 8, 60
TABLE_ORDERS = (8, 12, 16, 20)
TABLE_COMMISSIONS = (Decimal("0.10"), Decimal("0.12"), Decimal("0.15"))


@dataclass(frozen=True)
class SimulationResult:
    orders: int
    average_net_margin: Decimal
    losing_orders: int
    average_customer_savings: Decimal


@contextmanager
def _commission(fresh: Decimal):
    """SM-02: la comisión simulada vale solo dentro del bloque."""
    original = domain.COMMISSION["FRESCOS"]
    domain.COMMISSION["FRESCOS"] = fresh
    try:
        yield
    finally:
        domain.COMMISSION["FRESCOS"] = original


def simulate(orders: int, stop_cost: Decimal, fresh_commission: Decimal, costs: OperatingCosts,
             basket=BASKET) -> SimulationResult:
    """SM-01: un ciclo sintético de una zona, con las reglas reales."""
    with _commission(fresh_commission):
        store = pilot_store()
        for product_id, product in list(store.products.items()):  # sin límite de stock en la simulación
            store.products[product_id] = replace(product, max_available=Decimal("100000"))
        store.add_zone(Zone("Z-SIM", "Zona simulada", "Lince", "G-SIM", stop_cost))
        for i in range(orders):
            customer_id = 90000 + i
            store.add_customer(Customer(customer_id, f"Vecino simulado {i}", "Z-SIM"))
            order = register_order(store, customer_id=customer_id, lines=basket, payment_method="PLIN",
                                   operation_code=f"SIM-{i}", amount=quote_order(store, basket).total, now=WHEN)
            verify_payment(store, order.order_id, now=WHEN)
        cycle = cycle_id(WHEN)
        settle_cycle(store, cycle, at=WHEN)
        summary = net_margin_summary(store, cycle, costs)
        savings = delivered_savings(store, cycle)
    return SimulationResult(orders, summary.average_net_margin, summary.losing_orders, savings.total / orders)


def break_even_orders(stop_cost: Decimal, fresh_commission: Decimal, costs: OperatingCosts) -> int | None:
    """SM-03: mínimo de pedidos por zona para no perder plata (None si ni con 60 alcanza)."""
    for orders in range(MIN_ORDERS, MAX_ORDERS + 1):
        if simulate(orders, stop_cost, fresh_commission, costs).average_net_margin >= 0:
            return orders
    return None


def decision_table(stop_cost: Decimal) -> dict[str, dict[tuple[int, Decimal], Decimal]]:
    """SM-04: margen neto promedio por (pedidos, comisión), en los dos escenarios."""
    table = {}
    for costs in (OPTIMISTIC, PESSIMISTIC):
        table[costs.name] = {
            (orders, commission): simulate(orders, stop_cost, commission, costs).average_net_margin
            for orders in TABLE_ORDERS for commission in TABLE_COMMISSIONS
        }
    return table


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    stop_cost = Decimal(sys.argv[1]) if len(sys.argv) > 1 else Decimal("40")
    print(f"Margen neto promedio por pedido (S/), parada de S/ {stop_cost}, canasta de S/ 61")
    for scenario, cells in decision_table(stop_cost).items():
        print(f"\n{scenario}")
        print("pedidos  " + "".join(f"{f'{c * 100:.0f} %':>10}" for c in TABLE_COMMISSIONS))
        for orders in TABLE_ORDERS:
            row = "".join(f"{cells[(orders, c)].quantize(Decimal('0.01')):>10}" for c in TABLE_COMMISSIONS)
            print(f"{orders:>7}  {row}")
    print("\nMínimo de pedidos por zona para no perder (comisión 12 %):")
    for costs in (OPTIMISTIC, PESSIMISTIC):
        minimum = break_even_orders(stop_cost, Decimal("0.12"), costs)
        print(f"  {costs.name}: {minimum if minimum else f'no alcanza ni con {MAX_ORDERS}'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
