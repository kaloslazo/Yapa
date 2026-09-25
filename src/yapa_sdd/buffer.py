"""Colchón de reposición con tope de monto (iteración 7).

Spec: docs/desarrollo/07-armado-entrega-reclamos.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .domain import BusinessRuleError
from .fulfillment import check_staff
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


def buffer_value(store: InMemoryStore) -> Decimal:
    return sum((stock.value for stock in store.buffer.values()), Decimal("0"))


def _quantity(quantity, step: Decimal) -> Decimal:
    """CO-03: mayor que cero y en el paso del producto."""
    value = _to_quantity(quantity)
    if value <= 0 or value % step != 0:
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


def use_buffer(store: InMemoryStore, product_id: str, quantity, *, by: str) -> BufferStock:
    """CO-05: reponer un faltante con lo guardado; el valor baja en proporción."""
    check_staff(store, by)  # CO-01
    stock = store.buffer.get(product_id)
    if stock is None:
        raise BusinessRuleError("BUFFER_INSUFFICIENT", f"No hay {product_id} en el colchón.")
    value = _quantity(quantity, stock.step)
    if value > stock.quantity:
        raise BusinessRuleError("BUFFER_INSUFFICIENT", f"Solo hay {stock.quantity} de {product_id} en el colchón.")
    remaining = stock.quantity - value
    stock.value = stock.value * remaining / stock.quantity
    stock.quantity = remaining
    return stock
