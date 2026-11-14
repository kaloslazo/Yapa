"""Compra real con faltantes y dañados al armar (iteración 56).

Spec: docs/desarrollo/56-compra-real-y-armado.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from . import cycle as cycles
from . import partners
from .buffer import NON_PERISHABLE, BufferUse
from .domain import BusinessRuleError, is_multiple
from .fulfillment import check_photo, check_role, is_attended
from .order_registration import _to_quantity
from .store import InMemoryStore


ZERO = Decimal("0")


@dataclass(frozen=True)
class Purchase:
    cycle: str
    received: dict  # producto -> cantidad que llegó (solo lo que faltó, S-295)
    by: str
    at: datetime


@dataclass(frozen=True)
class Shortage:
    """Lo que no llega a un pedido: de la compra o dañado al armar (S-296, S-297)."""

    cycle: str
    order_id: int
    product_id: str
    quantity: Decimal
    from_buffer: Decimal  # lo que repuso el colchón; el resto es faltante en la liquidación
    source: str  # COMPRA o DANADO
    by: str
    at: datetime
    photo: str = ""


def _taken(store: InMemoryStore, order_id: int, product_id: str) -> Decimal:
    return sum((s.quantity for s in store.shortages if s.order_id == order_id and s.product_id == product_id), ZERO)


def _from_buffer(store: InMemoryStore, cycle: str, order_id: int, product_id: str, quantity: Decimal, by: str,
                 now: datetime) -> Decimal:
    """S-296, S-297: el colchón repone primero, solo lo no perecible y lo que haya."""
    stock = store.buffer.get(product_id)
    product = store.catalog_for(cycle).get(product_id)
    category = product.category if product else None
    if stock is None or stock.quantity <= 0 or category not in NON_PERISHABLE:
        return ZERO
    used = min(quantity, stock.quantity)
    value = stock.value * used / stock.quantity
    stock.value -= value
    stock.quantity -= used
    store.buffer_uses.append(BufferUse(order_id, product_id, used, value, by, now))  # S-122
    return used


def _add(store: InMemoryStore, cycle: str, order_id: int, product_id: str, quantity: Decimal, source: str, by: str,
         now: datetime, photo: str = "") -> Shortage:
    covered = _from_buffer(store, cycle, order_id, product_id, quantity, by, now)
    shortage = Shortage(cycle, order_id, product_id, quantity, covered, source, by, now, photo)
    store.shortages.append(shortage)
    return shortage


def register_purchase(store: InMemoryStore, cycle: str, received: dict, *, by, now: datetime) -> Purchase:
    check_role(store, by, partners.BUYER)  # CR-01
    cycles.check_cycle_id(cycle)
    if cycles.to_lima(now) < cycles.closes_at(cycle):  # CR-02
        raise BusinessRuleError("CYCLE_STILL_OPEN", "El ciclo sigue abierto; la compra se registra después del cierre.")
    if cycle in store.purchases:  # CR-03
        raise BusinessRuleError("PURCHASE_ALREADY_REGISTERED", "La compra de esta semana ya está registrada.")
    attended = sorted((o for o in store.orders_in_cycle(cycle) if is_attended(store, o)),
                      key=lambda o: o.order_id, reverse=True)
    catalog = store.catalog_for(cycle)
    shortfalls = {}
    for product_id, value in dict(received or {}).items():  # CR-04: todo se valida antes de aplicar
        ordered = sum((line.quantity for o in attended for line in o.lines if line.product_id == product_id), ZERO)
        try:
            quantity = _to_quantity(value)
        except BusinessRuleError:
            quantity = None
        product = catalog.get(product_id)
        if (quantity is None or ordered == 0 or product is None or quantity < 0 or quantity > ordered
                or not is_multiple(quantity, product.step)):
            raise BusinessRuleError("INVALID_PURCHASE_ITEM", f"Cantidad recibida no válida para {product_id}: {value}.")
        shortfalls[product_id] = ordered - quantity
    for product_id, missing in shortfalls.items():  # S-296: desde el último pedido registrado
        for order in attended:
            if missing <= 0:
                break
            line_quantity = sum((l.quantity for l in order.lines if l.product_id == product_id), ZERO)
            take = min(line_quantity - _taken(store, order.order_id, product_id), missing)
            if take > 0:
                _add(store, cycle, order.order_id, product_id, take, "COMPRA", by, now)
                missing -= take
    result = Purchase(cycle, {p: Decimal(str(v)) for p, v in dict(received or {}).items()}, by, now)
    store.purchases[cycle] = result
    return result


def register_damaged(store: InMemoryStore, order_id: int, product_id: str, quantity, *, by, photo: str,
                     now: datetime) -> Shortage:
    check_role(store, by, partners.PACKER)  # DA-01
    order = store.orders.get(order_id)
    if order is None:  # DA-02
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    if cycles.to_lima(now) < cycles.closes_at(order.cycle):
        raise BusinessRuleError("CYCLE_STILL_OPEN", "Todavía no puedes registrar productos dañados: esta semana sigue recibiendo compras. El armado se habilita el miércoles a las 8 p. m. (hora de Lima).")
    if not is_attended(store, order):
        raise BusinessRuleError("ORDER_NOT_ATTENDED", "Este pedido no se atiende en este ciclo.")
    closed = (order.cycle, order.zone_id)
    if closed in store.deliveries or closed in store.failed_deliveries:
        raise BusinessRuleError("ZONE_ALREADY_CLOSED", "La zona ya se entregó o falló; lo que falte va por reclamo.")
    if order.cycle not in store.purchases:  # DA-03
        raise BusinessRuleError("PURCHASE_NOT_REGISTERED", "Primero compras registra lo que llegó del proveedor.")
    photo = check_photo(photo)  # DA-04
    ordered = sum((l.quantity for l in order.lines if l.product_id == product_id), ZERO)
    product = store.catalog_for(order.cycle).get(product_id)
    try:
        value = _to_quantity(quantity)
    except BusinessRuleError:
        value = None
    if (value is None or ordered == 0 or product is None or value <= 0 or not is_multiple(value, product.step)
            or _taken(store, order_id, product_id) + value > ordered):  # DA-05
        raise BusinessRuleError("INVALID_DAMAGED_ITEM", f"Cantidad dañada no válida para {product_id}: {quantity}.")
    return _add(store, order.cycle, order_id, product_id, value, "DANADO", by, now, photo)  # DA-06


def missing_for_settlement(store: InMemoryStore, cycle: str) -> list[tuple[int, str, Decimal]]:
    """CR-06: lo que el colchón no cubrió pasa a la liquidación como faltante (LQ-06)."""
    return [(s.order_id, s.product_id, s.quantity - s.from_buffer) for s in store.shortages
            if s.cycle == cycle and s.quantity > s.from_buffer]
