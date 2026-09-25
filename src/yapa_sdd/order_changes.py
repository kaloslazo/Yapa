"""Cancelar y editar el pedido antes del cierre (iteración 4).

Spec: docs/desarrollo/04-cancelar-editar.md.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Iterable

from . import cycle, wallet
from .domain import BusinessRuleError, Order, Payment
from .order_registration import _check_balance_use, _check_payment, quote_order
from .store import InMemoryStore


REFUND_DESTINATIONS = frozenset({"MEDIO_DE_PAGO", "SALDO"})  # S-19


def _editable_order(store: InMemoryStore, order_id: int, customer_id: int, now: datetime) -> Order:
    order = store.orders.get(order_id)
    if order is None or order.customer_id != customer_id:  # CE-01
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    if order.status != "REGISTRADO":  # CE-02
        raise BusinessRuleError("ORDER_NOT_EDITABLE", "Este pedido ya no se puede cambiar.")
    if not cycle.is_open(now) or cycle.cycle_id(now) != order.cycle:  # CE-03, S-18
        raise BusinessRuleError("CYCLE_CLOSED", "El ciclo ya cerró; el pedido no se puede cambiar.")
    return order


def cancel_order(store: InMemoryStore, order_id: int, *, customer_id: int, now: datetime,
                 refund_to: str = "MEDIO_DE_PAGO") -> Order:
    order = _editable_order(store, order_id, customer_id, now)
    if refund_to not in REFUND_DESTINATIONS:
        raise BusinessRuleError("INVALID_REFUND_DESTINATION", "Elige devolver a tu medio de pago o a tu saldo.")

    for line in order.lines:  # CE-04
        store.release(line.product_id, line.quantity, order.cycle)
    reference = f"cancelación pedido {order.order_id}"
    for payment in order.payments:  # CE-05
        if payment.method == "SALDO":
            wallet.credit(store, customer_id, payment.amount, "DEVOLUCION_A_SALDO", now, reference)
        elif payment.status == "VERIFICADO":
            if refund_to == "SALDO":
                wallet.credit(store, customer_id, payment.amount, "DEVOLUCION_A_SALDO", now, reference)
            else:
                wallet.add_refund(store, customer_id, payment.amount, "CANCELACION_CLIENTE", now)
        # S-20: pago externo sin verificar -> sin reembolso automático
    order.status = "CANCELADO_POR_CLIENTE"
    return order


def _reduce_payments(order: Order, amount: Decimal) -> Decimal:
    """S-24: reduce pagos por `amount` y devuelve cuánto era dinero confirmado."""
    def priority(payment: Payment) -> int:
        if payment.method != "SALDO" and payment.status != "VERIFICADO":
            return 0
        return 1 if payment.method == "SALDO" else 2

    confirmed = Decimal("0")
    for payment in sorted(order.payments, key=priority):
        if amount <= 0:
            break
        cut = min(payment.amount, amount)
        payment.amount -= cut
        amount -= cut
        if priority(payment) > 0:
            confirmed += cut
    order.payments = [p for p in order.payments if p.amount > 0]
    return confirmed


def edit_order(store: InMemoryStore, order_id: int, *, customer_id: int, lines: Iterable, now: datetime,
               payment_method: str | None = None, operation_code: str | None = None, amount=Decimal("0"),
               use_balance=Decimal("0")) -> Order:
    order = _editable_order(store, order_id, customer_id, now)

    # CE-08: lo que este pedido ya reservó cuenta como disponible mientras se cotiza
    for line in order.lines:
        store.release(line.product_id, line.quantity, order.cycle)
    try:
        kept = {line.product_id: line.quantity for line in order.lines}  # S-39
        quote = quote_order(store, lines, order.cycle, kept)
        difference = quote.total - order.total
        new_payments = []
        if difference > 0:  # CE-10, S-23
            used = _check_balance_use(store, customer_id, use_balance, difference)
            external = difference - used
            if used > 0:
                new_payments.append(Payment("SALDO", used, status="VERIFICADO"))
            if external > 0:
                code = _check_payment(store, payment_method, operation_code, amount, external)
                new_payments.append(Payment(payment_method, external, code))
            elif Decimal(str(amount or 0)) != 0:
                raise BusinessRuleError("PAYMENT_AMOUNT_MISMATCH", "El saldo ya cubre la diferencia.")
        elif Decimal(str(amount or 0)) != 0 or Decimal(str(use_balance or 0)) != 0:
            raise BusinessRuleError("PAYMENT_AMOUNT_MISMATCH", "El pedido no subió; no hay nada que pagar.")
    except BusinessRuleError:
        for line in order.lines:  # CE-11: todo vuelve como estaba
            store.reserve(line.product_id, line.quantity, order.cycle)
        raise

    for line in quote.lines:
        store.reserve(line.product_id, line.quantity, order.cycle)
    reference = f"edición pedido {order.order_id}"
    if difference < 0:  # CE-09, CE-12
        confirmed = _reduce_payments(order, -difference)
        wallet.credit(store, customer_id, confirmed, "DEVOLUCION_A_SALDO", now, reference)
    for payment in new_payments:
        order.payments.append(payment)
        if payment.method == "SALDO":
            wallet.debit(store, customer_id, payment.amount, "USO_EN_PEDIDO", now, reference)
        else:
            store.used_codes.add(payment.operation_code)
    order.lines = quote.lines
    order.subtotal = quote.subtotal
    order.total = quote.total
    return order
