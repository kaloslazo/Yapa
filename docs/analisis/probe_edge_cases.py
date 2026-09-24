"""Casos borde de register_weekly_order (repo sdd-2026-exposicion).

Aplica al codigo de la iteracion 1 (commit bd48598). Para reproducirlo:
    git worktree add ../iter1 bd48598
    cd ../iter1 && PYTHONPATH=src python ../sdd-2026-exposicion/docs/analisis/probe_edge_cases.py
"""
from datetime import datetime
from decimal import Decimal as D

from yapa_sdd.order_registration import (
    CatalogItem, CustomerAddress, DeliveryWindow, OrderLine,
    OrderRegistrationError, register_weekly_order,
)

NOW = datetime(2026, 9, 16, 10)
START = datetime(2026, 9, 14)
CLOSE = datetime(2026, 9, 16, 20)


def item(**k):
    base = dict(product_id=10, name="Arroz", unit="kg", unit_price=D("30"), active=True,
                valid_from=datetime(2026, 9, 1), valid_until=datetime(2026, 9, 30))
    base.update(k)
    return CatalogItem(**base)


def run(label, **over):
    values = dict(order_id=1, address=CustomerAddress("Lince", True),
                  lines=[OrderLine(item(), D("2"))],
                  delivery_window=DeliveryWindow("SAT_09_12", 30, 5),
                  payment_method="TRANSFERENCIA", now=NOW, cycle_start=START, cycle_close=CLOSE)
    values.update(over)
    try:
        order = register_weekly_order(**values)
        print(f"{label:48} OK total={order.total}")
    except OrderRegistrationError as e:
        print(f"{label:48} {e.code}")


run("D1 ventana inexistente SUN_09_12", delivery_window=DeliveryWindow("SUN_09_12", 30, 0))
run("D2 direccion Lince no validada", address=CustomerAddress("Lince", False))
run("D3 'Jesus Maria' sin tildes", address=CustomerAddress("Jesus Maria", True))
run("D4 carrito vacio", lines=[])
run("D4 cantidad 0", lines=[OrderLine(item(), D("0")), OrderLine(item(), D("2"))])
run("D5 0.001 unidades", lines=[OrderLine(item(unit="unidad", unit_price=D("60000")), D("0.001"))])
run("D6 subtotal 49.995 (redondeo)", lines=[OrderLine(item(unit_price=D("49.995")), D("1"))])
run("D7 now == cierre exacto", now=CLOSE)
run("D8 ciclo arbitrario jueves-viernes", now=datetime(2026, 9, 18, 10),
    cycle_start=datetime(2026, 9, 17), cycle_close=datetime(2026, 9, 19))
run("D10 ventana llena + subtotal bajo", delivery_window=DeliveryWindow("SAT_09_12", 1, 1),
    lines=[OrderLine(item(unit_price=D("1")), D("1"))])
run("D11 mismo producto en 2 lineas", lines=[OrderLine(item(), D("1")), OrderLine(item(), D("1"))])
