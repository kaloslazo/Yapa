"""Logística propia de Yapa: flete de compra, salida a reparto y seguimiento del pedido (iteración 58).

Spec: docs/desarrollo/58-logistica-propia.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from . import cycle as cycles
from . import notices, partners
from .domain import BusinessRuleError, Order
from .fulfillment import _check_purchase, _ready_orders, check_courier, check_role, is_attended
from .metrics import OperatingCosts
from .store import InMemoryStore


ESTIMATED_FREIGHT = Decimal("180")  # S-307: cotización más baja encontrada el 09/11/2026 (S/ 180–320)
MAX_FREIGHT = Decimal("2000")  # S-306
PACKING, SUPPORT = Decimal("1.60"), Decimal("0.73")  # S-307: los mismos de S-96 y S-97
STEPS = ("Pedido", "Pago verificado", "Comprado", "Armado", "En camino", "Entregado", "Te devolvemos")  # S-309


@dataclass(frozen=True)
class Freight:
    cycle: str
    company: str
    amount: Decimal
    by: str
    at: datetime


@dataclass(frozen=True)
class Dispatch:
    cycle: str
    zone_id: str
    order_ids: tuple[int, ...]
    by: str
    at: datetime


def register_freight(store: InMemoryStore, cycle: str, company, amount, *, by, now: datetime) -> Freight:
    check_role(store, by, partners.BUYER)  # FL-01
    cycles.check_cycle_id(cycle)
    if cycles.to_lima(now) < cycles.closes_at(cycle):  # FL-02
        raise BusinessRuleError("CYCLE_STILL_OPEN", "El ciclo sigue abierto; el flete se registra después del cierre.")
    if cycle in store.freights:  # FL-03
        raise BusinessRuleError("FREIGHT_ALREADY_REGISTERED", "El flete de esta semana ya está registrado.")
    name = str(company or "").strip()
    if not name or len(name) > 80:  # FL-04
        raise BusinessRuleError("INVALID_FREIGHT", "Escribe el nombre de la empresa del flete (hasta 80 caracteres).")
    try:
        value = Decimal(str(amount).strip())
    except (InvalidOperation, ValueError):
        value = None
    if value is None or not value.is_finite() or value <= 0 or value > MAX_FREIGHT or value.as_tuple().exponent < -2:
        raise BusinessRuleError("INVALID_AMOUNT", f"El monto del flete va de S/ 0.01 a S/ {MAX_FREIGHT}, con céntimos.")
    freight = Freight(cycle, name, value.quantize(Decimal("0.01")), by, now)
    store.freights[cycle] = freight
    return freight


def real_costs(store: InMemoryStore, cycle: str) -> tuple[OperatingCosts, Decimal, bool]:
    """MR-01, S-307: el flete de la semana repartido entre los pedidos atendidos; sin registrar, S/ 180 estimados."""
    registered = store.freights.get(cycle)
    freight = registered.amount if registered else ESTIMATED_FREIGHT
    attended = sum(1 for o in store.orders_in_cycle(cycle) if is_attended(store, o))
    trip = (freight / attended).quantize(Decimal("0.01")) if attended else Decimal("0")
    return OperatingCosts("REAL", trip, PACKING, SUPPORT, Decimal("0")), freight, registered is None


def dispatch_zone(store: InMemoryStore, cycle: str, zone_id: str, *, by, now: datetime) -> Dispatch:
    """SR-01, SR-02, S-308: el reparto sale hacia la zona y cada vecino recibe el aviso."""
    check_courier(store, by)
    if zone_id not in store.zones:
        raise BusinessRuleError("ZONE_NOT_FOUND", "La zona no existe.")
    if (cycle, zone_id) in store.deliveries or (cycle, zone_id) in store.failed_deliveries:
        raise BusinessRuleError("ZONE_ALREADY_CLOSED", "Esta zona ya se entregó o ya falló en el ciclo.")
    if (cycle, zone_id) in store.dispatches:
        raise BusinessRuleError("ZONE_ALREADY_DISPATCHED", "El reparto ya salió hacia esta zona.")
    orders = _ready_orders(store, cycle, zone_id)
    _check_purchase(store, cycle)
    dispatch = Dispatch(cycle, zone_id, tuple(o.order_id for o in orders), by, now)
    store.dispatches[(cycle, zone_id)] = dispatch
    zone = store.zones[zone_id].name
    for order in orders:
        notices.add(store, order.customer_id, "EN_CAMINO", "Tu pedido va en camino",
                    f"Tu pedido {order.order_id} de la semana {cycle} ya salió hacia {zone}.", now)
    return dispatch


def tracking(store: InMemoryStore, order: Order) -> list[dict]:
    """SG-01, S-309: los siete pasos del pedido y cuáles ya pasaron."""
    key = (order.cycle, order.zone_id)
    delivered = key in store.deliveries and order.order_id in store.deliveries[key].order_ids
    done = (
        True,
        order.payment_status == "VERIFICADO",
        order.cycle in store.purchases,
        bool(store.bags.get(order.order_id)),
        key in store.dispatches or delivered,  # S-308: entregar sin marcar la salida también cuenta
        delivered,
        order.status == "LIQUIDADO",
    )
    return [{"paso": step, "hecho": value} for step, value in zip(STEPS, done)]
