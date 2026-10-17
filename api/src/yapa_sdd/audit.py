"""Conciliación del dinero (iteración 19).

Spec: docs/desarrollo/19-conciliacion-punta-a-punta.md (S-113..S-115):
recibido = en curso + retenido + deuda con clientes + devoluciones pagadas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .store import InMemoryStore
from .wallet import amount_owed


ZERO = Decimal("0")


@dataclass(frozen=True)
class CashEntry:
    """S-114: un pago externo verificado; no cambia aunque el pedido se edite o se cancele."""

    order_id: int
    method: str
    amount: Decimal
    operation_code: str
    at: datetime | None


@dataclass(frozen=True)
class MoneyBalance:
    received: Decimal
    in_flight: Decimal
    kept: Decimal
    owed: Decimal
    refunds_paid: Decimal
    difference: Decimal


def money_balance(store: InMemoryStore) -> MoneyBalance:
    """AU-02."""
    received = sum((entry.amount for entry in store.cash_in), ZERO)
    in_flight = sum((payment.amount for order in store.orders.values() if order.status == "REGISTRADO"
                     for payment in order.payments if payment.status == "VERIFICADO"), ZERO)
    kept = sum((settled.final_amount for result in store.settlements.values()
                for settled in result.orders.values() if settled.status in ("LIQUIDADO", "NO_ENTREGADO")), ZERO)
    kept -= sum((claim.refund_amount for claim in store.claims.values() if claim.status == "APROBADO"), ZERO)
    owed = amount_owed(store)
    refunds_paid = sum((refund.amount for refund in store.refunds.values() if refund.status == "PAGADO"), ZERO)
    difference = received - in_flight - kept - owed - refunds_paid
    return MoneyBalance(received, in_flight, kept, owed, refunds_paid, difference)
