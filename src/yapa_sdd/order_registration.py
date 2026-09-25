"""CUN-02 Registrar pedido semanal y límite de CUN-03 (iteración 2).

Spec: docs/sdd/02-especificacion-cun-02.md. Cada validación indica la regla
que implementa; el orden de las llamadas es el orden de S-11.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable

from . import cycle
from .domain import (
    MAX_DELIVERY_FEE,
    MAX_QUANTITY,
    MIN_SUBTOTAL,
    PAYMENT_METHODS,
    PILOT_DISTRICTS,
    BusinessRuleError,
    Customer,
    Order,
    OrderLine,
    Payment,
    Product,
    Zone,
    ceil_cents,
    floor_cents,
)
from .store import InMemoryStore
from . import wallet


@dataclass(frozen=True)
class Quote:
    lines: list[OrderLine]
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal


def _customer(store: InMemoryStore, customer_id: int) -> Customer:
    customer = store.customers.get(customer_id)
    if customer is None:
        raise BusinessRuleError("CUSTOMER_NOT_FOUND", "El cliente no está registrado.")
    if customer.suspended:
        raise BusinessRuleError("CUSTOMER_SUSPENDED", "El cliente está suspendido y no puede hacer pedidos.")
    return customer


def _zone(store: InMemoryStore, customer: Customer) -> Zone:
    zone = store.zones.get(customer.zone_id)
    if zone is None or not zone.reception_accepted or zone.district not in PILOT_DISTRICTS:
        raise BusinessRuleError("ZONE_NOT_AVAILABLE", "Tu zona todavía no está disponible para pedidos.")
    return zone


def _check_cycle(now: datetime) -> None:
    if not cycle.is_open(now):
        raise BusinessRuleError("CYCLE_CLOSED", "El ciclo semanal está cerrado. Vuelve el lunes.")


def _to_quantity(value) -> Decimal:
    try:
        quantity = Decimal(str(value))
    except InvalidOperation:
        quantity = None
    if quantity is None or not quantity.is_finite():
        raise BusinessRuleError("INVALID_QUANTITY", f"Cantidad no válida: {value}.")
    return quantity


def _merge_lines(lines: Iterable) -> list[tuple[str, Decimal]]:
    """RP-05: al menos una línea; un producto repetido se suma."""
    merged: dict[str, Decimal] = {}
    for product_id, quantity in lines:
        merged[product_id] = merged.get(product_id, Decimal("0")) + _to_quantity(quantity)
    if not merged:
        raise BusinessRuleError("EMPTY_ORDER", "El pedido debe tener al menos un producto.")
    return list(merged.items())


def _product(store: InMemoryStore, product_id: str) -> Product:
    """RP-06: el producto está en el catálogo del ciclo y activo."""
    product = store.products.get(product_id)
    if product is None or not product.active:
        raise BusinessRuleError("PRODUCT_NOT_AVAILABLE", f"{product_id} no está disponible este ciclo.")
    return product


def _check_quantity(product: Product, quantity: Decimal) -> None:
    """RP-07: mayor que cero, múltiplo del paso y dentro del tope por línea."""
    if quantity <= 0 or quantity % product.step != 0 or quantity > MAX_QUANTITY[product.unit]:
        raise BusinessRuleError(
            "INVALID_QUANTITY",
            f"{product.name}: se pide en pasos de {product.step} {product.unit}, "
            f"hasta {MAX_QUANTITY[product.unit]} {product.unit}.",
        )


def _check_stock(store: InMemoryStore, product: Product, quantity: Decimal) -> None:
    """RP-08: nunca vender más de lo que el proveedor declaró."""
    if store.reserved_quantity(product.product_id) + quantity > product.max_available:
        raise BusinessRuleError("PRODUCT_SOLD_OUT", f"{product.name} está agotado este ciclo.")


def quote_order(store: InMemoryStore, lines: Iterable) -> Quote:
    """Cotización: RP-05..RP-11 sin reservar stock ni crear el pedido."""
    order_lines = []
    for product_id, quantity in _merge_lines(lines):
        product = _product(store, product_id)
        _check_quantity(product, quantity)
        _check_stock(store, product, quantity)
        order_lines.append(OrderLine(product_id, quantity, product.max_unit_price()))  # RP-09

    subtotal = sum((line.max_total for line in order_lines), Decimal("0"))
    if subtotal < MIN_SUBTOTAL:  # RP-10: se compara el valor exacto
        raise BusinessRuleError(
            "SUBTOTAL_BELOW_MINIMUM",
            f"El pedido mínimo es S/ {MIN_SUBTOTAL}. Faltan S/ {ceil_cents(MIN_SUBTOTAL - subtotal)}.",
        )

    total = floor_cents(subtotal + MAX_DELIVERY_FEE)  # RP-11
    return Quote(order_lines, subtotal, MAX_DELIVERY_FEE, total)


def _check_payment(store: InMemoryStore, method: str, operation_code: str, amount, total: Decimal) -> str:
    if method not in PAYMENT_METHODS:  # RP-12
        raise BusinessRuleError("PAYMENT_METHOD_NOT_ALLOWED", "Solo se acepta Yape o Plin.")
    code = (operation_code or "").strip()
    if not code:  # RP-13
        raise BusinessRuleError("PAYMENT_CODE_REQUIRED", "Ingresa el código de operación de tu pago.")
    if code in store.used_codes:
        raise BusinessRuleError("PAYMENT_CODE_ALREADY_USED", "Ese código de operación ya fue usado en otro pedido.")
    try:
        paid = Decimal(str(amount))
    except InvalidOperation:
        paid = None
    if paid != total:  # RP-14
        raise BusinessRuleError("PAYMENT_AMOUNT_MISMATCH", f"El monto pagado debe ser S/ {total}.")
    return code


def _check_balance_use(store: InMemoryStore, customer_id: int, use_balance, total: Decimal) -> Decimal:
    """BS-03 y BS-04: el saldo usado existe y no pasa del total."""
    used = Decimal(str(use_balance or 0))
    if used < 0 or used > wallet.balance(store, customer_id):
        raise BusinessRuleError("INSUFFICIENT_BALANCE", "No tienes saldo suficiente.")
    if used > total:
        raise BusinessRuleError("BALANCE_EXCEEDS_TOTAL", f"El saldo a usar no puede pasar de S/ {total}.")
    return used


def register_order(
    store: InMemoryStore,
    *,
    customer_id: int,
    lines: Iterable,
    payment_method: str | None,
    operation_code: str | None,
    amount,
    now: datetime,
    use_balance=Decimal("0"),
) -> Order:
    customer = _customer(store, customer_id)  # RP-01
    zone = _zone(store, customer)  # RP-02
    _check_cycle(now)  # RP-03
    cycle_id = cycle.cycle_id(now)
    if store.find_order(customer_id, cycle_id):  # RP-04
        raise BusinessRuleError("ORDER_ALREADY_EXISTS", "Ya tienes un pedido en este ciclo.")

    quote = quote_order(store, lines)
    used = _check_balance_use(store, customer_id, use_balance, quote.total)
    external_due = quote.total - used  # BS-05
    payments = []
    if used > 0:
        payments.append(Payment("SALDO", used, status="VERIFICADO"))
    if external_due > 0:
        code = _check_payment(store, payment_method, operation_code, amount, external_due)
        payments.append(Payment(payment_method, external_due, code))
    elif Decimal(str(amount or 0)) != 0:  # BS-06: el saldo cubre todo
        raise BusinessRuleError("PAYMENT_AMOUNT_MISMATCH", "El saldo ya cubre el total; no hay que yapear.")

    for line in quote.lines:
        store.reserve(line.product_id, line.quantity)
    for payment in payments:
        if payment.operation_code:
            store.used_codes.add(payment.operation_code)
    order = Order(
        order_id=0,
        cycle=cycle_id,
        customer_id=customer.customer_id,
        zone_id=zone.zone_id,
        lines=quote.lines,
        subtotal=quote.subtotal,
        delivery_fee=quote.delivery_fee,
        total=quote.total,
        payments=payments,
    )
    order = store.save_new_order(order)
    wallet.debit(store, customer_id, used, "USO_EN_PEDIDO", now, f"pedido {order.order_id}")  # BS-07
    return order


def verify_payment(store: InMemoryStore, order_id: int, *, now: datetime) -> Order:
    """RP-15: el administrador confirma el código de operación antes del cierre."""
    order = store.orders.get(order_id)
    if order is None:
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    if not cycle.is_open(now) or cycle.cycle_id(now) != order.cycle:
        raise BusinessRuleError("CYCLE_CLOSED", "El ciclo ya cerró; el pago no puede verificarse.")
    for payment in order.payments:
        payment.status = "VERIFICADO"
    return order
