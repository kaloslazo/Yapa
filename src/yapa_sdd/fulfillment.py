"""Armado con foto por bolsa y entrega en portería (iteración 7).

Spec: docs/desarrollo/07-armado-entrega-reclamos.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from . import cycle as cycles
from .domain import MIN_ORDERS_PER_GROUP, BusinessRuleError, Order
from .store import InMemoryStore


@dataclass(frozen=True)
class Bag:
    order_id: int
    number: int
    photo: str
    packed_by: str
    packed_at: datetime


@dataclass(frozen=True)
class Delivery:
    cycle: str
    zone_id: str
    order_ids: tuple[int, ...]
    photo: str
    received_by: str
    reception_kind: str
    delivered_by: str
    delivered_at: datetime


def check_staff(store: InMemoryStore, by: str) -> None:
    """S-40: el personal de Yapa son los administradores."""
    if by not in store.admins:
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo el personal de Yapa puede hacer esto.")


def check_photo(photo: str | None) -> str:
    photo = (photo or "").strip()
    if not photo:
        raise BusinessRuleError("PHOTO_REQUIRED", "Falta la foto.")
    return photo


def _takes_part(order: Order) -> bool:
    return order.status != "CANCELADO_POR_CLIENTE" and order.payment_status == "VERIFICADO"


def is_attended(store: InMemoryStore, order: Order) -> bool:
    """S-41: el mismo criterio de la liquidación (LQ-01, LQ-02, CE-07)."""
    if not _takes_part(order):
        return False
    group = store.zones[order.zone_id].group_id
    in_group = [o for o in store.orders_in_cycle(order.cycle)
                if _takes_part(o) and store.zones[o.zone_id].group_id == group]
    return len(in_group) >= MIN_ORDERS_PER_GROUP


def pack_bag(store: InMemoryStore, order_id: int, *, by: str, photo: str, now: datetime) -> Bag:
    check_staff(store, by)  # AR-01
    order = store.orders.get(order_id)
    if order is None:  # AR-02
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    if cycles.to_lima(now) < cycles.closes_at(order.cycle):  # AR-03
        raise BusinessRuleError("CYCLE_STILL_OPEN", "El ciclo sigue abierto; todavía no se arma.")
    if not is_attended(store, order):  # AR-04
        raise BusinessRuleError("ORDER_NOT_ATTENDED", "Este pedido no se atiende en este ciclo.")
    photo = check_photo(photo)  # AR-05
    bags = store.bags.setdefault(order_id, [])
    bag = Bag(order_id, len(bags) + 1, photo, by, now)
    bags.append(bag)
    return bag


def deliver_zone(store: InMemoryStore, cycle: str, zone_id: str, *, by: str, photo: str, received_by: str,
                 now: datetime) -> Delivery:
    check_staff(store, by)  # EN-01
    zone = store.zones.get(zone_id)
    if zone is None:  # EN-02
        raise BusinessRuleError("ZONE_NOT_FOUND", "La zona no existe.")
    if (cycle, zone_id) in store.deliveries:
        raise BusinessRuleError("ZONE_ALREADY_DELIVERED", "Esta zona ya fue entregada en el ciclo.")
    photo = check_photo(photo)  # EN-03
    receiver = (received_by or "").strip()
    if not receiver:
        raise BusinessRuleError("RECEIVER_REQUIRED", "Registra el nombre de quien recibe.")
    orders = [o for o in store.orders_in_cycle(cycle) if o.zone_id == zone_id and is_attended(store, o)]
    if not orders:  # EN-04
        raise BusinessRuleError("NOTHING_TO_DELIVER", "La zona no tiene pedidos para entregar.")
    if any(not store.bags.get(order.order_id) for order in orders):  # EN-05
        raise BusinessRuleError("ORDERS_NOT_PACKED", "Hay pedidos de la zona sin armar.")
    delivery = Delivery(cycle, zone_id, tuple(o.order_id for o in orders), photo, receiver,
                        zone.reception_kind, by, now)
    store.deliveries[(cycle, zone_id)] = delivery
    return delivery
