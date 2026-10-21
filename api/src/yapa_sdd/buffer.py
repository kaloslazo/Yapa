"""Colchón de reposición con tope de monto (iteración 7).

Spec: docs/desarrollo/07-armado-entrega-reclamos.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .domain import BusinessRuleError, is_multiple
from .fulfillment import check_staff, is_attended
from .order_registration import _to_quantity
from .store import InMemoryStore


BUFFER_LIMIT = Decimal("500")  # S-46
NON_PERISHABLE = frozenset({"LIMPIEZA"})  # S-46


@dataclass
class BufferStock:
    product_id: str
    quantity: Decimal
    value: Decimal
    step: Decimal


@dataclass(frozen=True)
class BufferUse:
    """CO-08, S-122."""

    order_id: int
    product_id: str
    quantity: Decimal
    value: Decimal
    by: str
    at: datetime


def buffer_value(store: InMemoryStore) -> Decimal:
    return sum((stock.value for stock in store.buffer.values()), Decimal("0"))


def _quantity(quantity, step: Decimal) -> Decimal:
    """CO-03: mayor que cero y en el paso del producto."""
    value = _to_quantity(quantity)
    if value <= 0 or not is_multiple(value, step):
        raise BusinessRuleError("INVALID_QUANTITY", f"Cantidad no válida: {quantity}.")
    return value


def add_to_buffer(store: InMemoryStore, cycle: str, product_id: str, quantity, *, by: str) -> BufferStock:
    check_staff(store, by)  # CO-01
    product = store.catalog_for(cycle).get(product_id)
    if product is None:  # CO-02
        raise BusinessRuleError("PRODUCT_NOT_AVAILABLE", f"{product_id} no está en el catálogo del ciclo.")
    if product.category not in NON_PERISHABLE:
        raise BusinessRuleError("PERISHABLE_NOT_ALLOWED", f"{product.name} es perecible; no va al colchón.")
    value = _quantity(quantity, product.step)  # CO-03
    added_value = value * product.tiers[0].base_price  # S-46: precio del primer tramo
    if buffer_value(store) + added_value > BUFFER_LIMIT:  # CO-04
        raise BusinessRuleError("BUFFER_LIMIT_EXCEEDED", f"El colchón no puede pasar de S/ {BUFFER_LIMIT}.")
    stock = store.buffer.setdefault(product_id, BufferStock(product_id, Decimal("0"), Decimal("0"), product.step))
    stock.quantity += value
    stock.value += added_value
    return stock


def use_buffer(store: InMemoryStore, product_id: str, quantity, *, order_id: int, by: str,
               now: datetime) -> BufferStock:
    """CO-05: reponer un faltante de un pedido con lo guardado; el valor baja en proporción."""
    check_staff(store, by)  # CO-01
    order = store.orders.get(order_id)
    if order is None:  # CO-06
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    if not is_attended(store, order):
        raise BusinessRuleError("ORDER_NOT_ATTENDED", "Este pedido no se atiende en este ciclo.")
    stock = store.buffer.get(product_id)
    if stock is None:
        raise BusinessRuleError("BUFFER_INSUFFICIENT", f"No hay {product_id} en el colchón.")
    value = _quantity(quantity, stock.step)
    if value > stock.quantity:
        raise BusinessRuleError("BUFFER_INSUFFICIENT", f"Solo hay {stock.quantity} de {product_id} en el colchón.")
    ordered = sum((line.quantity for line in order.lines if line.product_id == product_id), Decimal("0"))
    replaced = sum((use.quantity for use in store.buffer_uses
                    if use.order_id == order_id and use.product_id == product_id), Decimal("0"))
    if replaced + value > ordered:  # CO-07
        raise BusinessRuleError("BUFFER_NOT_FOR_ORDER",
                                f"El pedido {order_id} pidió {ordered} de {product_id} y ya se repusieron {replaced}.")
    remaining = stock.quantity - value
    used_value = stock.value * value / stock.quantity
    stock.value -= used_value
    stock.quantity = remaining
    store.buffer_uses.append(BufferUse(order_id, product_id, value, used_value, by, now))  # CO-08
    return stock
