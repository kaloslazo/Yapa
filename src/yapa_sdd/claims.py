"""Reclamo por artículo dentro de 24 h y revisión caso por caso (iteración 7).

Spec: docs/desarrollo/07-armado-entrega-reclamos.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from . import wallet
from .domain import BusinessRuleError, Order, ceil_cents
from .fulfillment import check_photo, check_staff
from .store import InMemoryStore


CLAIM_WINDOW = timedelta(hours=24)  # S-43
CLAIM_REASONS = frozenset({"FALTANTE", "DANADO"})  # S-44


@dataclass
class Claim:
    claim_id: int
    order_id: int
    customer_id: int
    product_id: str
    quantity: Decimal
    reason: str
    photo: str
    filed_at: datetime
    status: str = "PENDIENTE"
    refund_amount: Decimal = Decimal("0")
    reviewed_by: str = ""
    reviewed_at: datetime | None = None


def _claimed(store: InMemoryStore, order_id: int, product_id: str, statuses: tuple[str, ...]) -> Decimal:
    return sum((c.quantity for c in store.claims.values()
                if c.order_id == order_id and c.product_id == product_id and c.status in statuses), Decimal("0"))


def _claim_quantity(store: InMemoryStore, order: Order, product_id: str, quantity) -> Decimal:
    """RC-05, S-44."""
    ordered = {line.product_id: line.quantity for line in order.lines}
    try:
        value = Decimal(str(quantity))
    except InvalidOperation:
        value = None
    valid = value is not None and value.is_finite() and product_id in ordered and value > 0
    if valid:
        step = store.catalog_for(order.cycle)[product_id].step
        already = _claimed(store, order.order_id, product_id, ("PENDIENTE", "APROBADO"))
        valid = value % step == 0 and already + value <= ordered[product_id]
    if not valid:
        raise BusinessRuleError("INVALID_CLAIM_ITEM", f"Reclamo no válido: {product_id}, {quantity}.")
    return value


def file_claim(store: InMemoryStore, order_id: int, *, customer_id: int, product_id: str, quantity, reason: str,
               photo: str, now: datetime) -> Claim:
    order = store.orders.get(order_id)
    if order is None or order.customer_id != customer_id:  # RC-01
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    delivery = store.deliveries.get((order.cycle, order.zone_id))
    if delivery is None or order_id not in delivery.order_ids:  # RC-02
        raise BusinessRuleError("ORDER_NOT_DELIVERED", "El pedido todavía no se entregó.")
    if now >= delivery.delivered_at + CLAIM_WINDOW:  # RC-03, S-43
        raise BusinessRuleError("CLAIM_WINDOW_CLOSED", "Pasaron las 24 horas para reclamar este pedido.")
    if reason not in CLAIM_REASONS:  # RC-04
        raise BusinessRuleError("INVALID_CLAIM_REASON", "Indica si el artículo faltó o llegó dañado.")
    photo = check_photo(photo)
    value = _claim_quantity(store, order, product_id, quantity)  # RC-05
    claim = Claim(store.next_claim_id(), order_id, customer_id, product_id, value, reason, photo, now)
    store.claims[claim.claim_id] = claim  # RC-06: queda pendiente, sin mover dinero
    return claim


def review_claim(store: InMemoryStore, claim_id: int, *, by: str, approve: bool, now: datetime) -> Claim:
    check_staff(store, by)  # RV-01
    claim = store.claims.get(claim_id)
    if claim is None:  # RV-02
        raise BusinessRuleError("CLAIM_NOT_FOUND", "El reclamo no existe.")
    if claim.status != "PENDIENTE":
        raise BusinessRuleError("CLAIM_ALREADY_REVIEWED", "Este reclamo ya fue revisado.")

    if approve:
        order = store.orders[claim.order_id]
        settlement = store.settlements.get(order.cycle)
        if settlement is None:  # RV-03
            raise BusinessRuleError("CYCLE_NOT_SETTLED", "Primero hay que liquidar el ciclo.")
        settled = settlement.orders.get(order.order_id)
        lines = {line.product_id: line for line in settled.lines} if settled else {}
        line = lines.get(claim.product_id)
        approved = _claimed(store, claim.order_id, claim.product_id, ("APROBADO",))
        if line is None or approved + claim.quantity > line.delivered:  # RV-04
            raise BusinessRuleError("INVALID_CLAIM_ITEM", "Esa cantidad ya no se entregó o ya se devolvió.")
        claim.refund_amount = ceil_cents(line.final_unit_price * claim.quantity)  # RV-05, S-45
        wallet.credit(store, claim.customer_id, claim.refund_amount, "RECLAMO_APROBADO", now,
                      f"reclamo {claim.claim_id}")
        claim.status = "APROBADO"
    else:
        claim.status = "RECHAZADO"
    claim.reviewed_by = by
    claim.reviewed_at = now
    return claim
