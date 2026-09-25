"""Billetera de saldo y reembolsos pendientes (iteración 3).

Spec: docs/desarrollo/03-billetera-saldo.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from .domain import BusinessRuleError
from .store import InMemoryStore


REFUND_DAYS = 30  # C-05, S-15


@dataclass(frozen=True)
class Movement:
    customer_id: int
    kind: str  # ABONO_LIQUIDACION, DEVOLUCION_A_SALDO, USO_EN_PEDIDO, DEVOLUCION_SOLICITADA
    amount: Decimal  # positivo = abono, negativo = cargo
    at: datetime | None
    reference: str = ""


@dataclass
class Refund:
    refund_id: int
    customer_id: int
    amount: Decimal
    reason: str
    requested_at: datetime | None
    due_date: datetime | None
    status: str = "PENDIENTE"
    operation_code: str = ""


def balance(store: InMemoryStore, customer_id: int) -> Decimal:
    """BS-01 y BS-02: suma de movimientos; no hay vencimiento."""
    return sum((m.amount for m in store.movements if m.customer_id == customer_id), Decimal("0"))


def credit(store: InMemoryStore, customer_id: int, amount: Decimal, kind: str, at=None, reference: str = "") -> None:
    if amount > 0:
        store.movements.append(Movement(customer_id, kind, amount, at, reference))


def debit(store: InMemoryStore, customer_id: int, amount: Decimal, kind: str, at=None, reference: str = "") -> None:
    if amount > balance(store, customer_id):
        raise BusinessRuleError("INSUFFICIENT_BALANCE", "No tienes saldo suficiente.")
    if amount > 0:
        store.movements.append(Movement(customer_id, kind, -amount, at, reference))


def add_refund(store: InMemoryStore, customer_id: int, amount: Decimal, reason: str, at=None) -> Refund:
    due = at + timedelta(days=REFUND_DAYS) if at else None
    refund = Refund(store.next_refund_id(), customer_id, amount, reason, at, due)
    store.refunds[refund.refund_id] = refund
    return refund


def request_withdrawal(store: InMemoryStore, customer_id: int, amount, now: datetime) -> Refund:
    """BS-12: el cliente pide de vuelta parte o todo su saldo."""
    amount = Decimal(str(amount))
    if amount <= 0:
        raise BusinessRuleError("INVALID_AMOUNT", "El monto a devolver debe ser mayor que cero.")
    debit(store, customer_id, amount, "DEVOLUCION_SOLICITADA", now)
    return add_refund(store, customer_id, amount, "SOLICITUD_CLIENTE", now)


def mark_refund_paid(store: InMemoryStore, refund_id: int, operation_code: str) -> Refund:
    """BS-13: el administrador registra la transferencia hecha."""
    refund = store.refunds.get(refund_id)
    if refund is None:
        raise BusinessRuleError("REFUND_NOT_FOUND", "El reembolso no existe.")
    if refund.status == "PAGADO":
        raise BusinessRuleError("REFUND_ALREADY_PAID", "Ese reembolso ya fue pagado.")
    refund.status = "PAGADO"
    refund.operation_code = operation_code
    return refund


def amount_owed(store: InMemoryStore) -> Decimal:
    """BS-14: saldos de clientes más reembolsos pendientes."""
    balances = sum((m.amount for m in store.movements), Decimal("0"))
    pending = sum((r.amount for r in store.refunds.values() if r.status == "PENDIENTE"), Decimal("0"))
    return balances + pending
