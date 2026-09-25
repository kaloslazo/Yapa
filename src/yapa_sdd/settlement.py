"""Liquidación del ciclo: "te devolvemos" (iteración 2).

Spec: docs/sdd/11-especificacion-liquidacion.md.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

from .domain import MAX_DELIVERY_FEE, MIN_ORDERS_PER_GROUP, BusinessRuleError, Order, floor_cents
from .store import InMemoryStore
from . import wallet


ZERO = Decimal("0")


@dataclass(frozen=True)
class SettledLine:
    product_id: str
    ordered: Decimal
    missing: Decimal
    delivered: Decimal
    final_unit_price: Decimal


@dataclass(frozen=True)
class SettledOrder:
    order_id: int
    status: str
    paid: Decimal
    lines: list[SettledLine] = field(default_factory=list)
    delivery_fee: Decimal = ZERO
    final_amount: Decimal = ZERO
    refund_amount: Decimal = ZERO
    refund_destination: str | None = None
    returned_to_balance: Decimal = ZERO


@dataclass(frozen=True)
class ProductSummary:
    product_id: str
    total_quantity: Decimal
    tier_min_quantity: Decimal
    final_unit_price: Decimal


@dataclass(frozen=True)
class CycleSettlement:
    cycle: str
    orders: dict[int, SettledOrder]
    products: dict[str, ProductSummary]
    total_credited: Decimal
    total_refunded: Decimal


def _missing_by_order(missing: Iterable, attended: dict[int, Order]) -> dict[tuple[int, str], Decimal]:
    """LQ-06: valida el reporte de faltantes y lo acumula por pedido y producto."""
    result: dict[tuple[int, str], Decimal] = {}
    for order_id, product_id, quantity in missing:
        quantity = Decimal(str(quantity))
        order = attended.get(order_id)
        ordered = {line.product_id: line.quantity for line in order.lines} if order else {}
        key = (order_id, product_id)
        total = result.get(key, ZERO) + quantity
        if quantity <= 0 or product_id not in ordered or total > ordered[product_id]:
            raise BusinessRuleError(
                "INVALID_MISSING_ITEM",
                f"Faltante no válido: pedido {order_id}, {product_id}, {quantity}.",
            )
        result[key] = total
    return result


def settle_cycle(store: InMemoryStore, cycle: str, missing: Iterable = (), at=None) -> CycleSettlement:
    if cycle in store.settled_cycles:  # BS-11
        raise BusinessRuleError("CYCLE_ALREADY_SETTLED", f"El ciclo {cycle} ya fue liquidado.")
    settled: dict[int, SettledOrder] = {}
    # CE-07: los cancelados por el cliente ya se resolvieron al cancelar
    orders = [o for o in store.orders_in_cycle(cycle) if o.status != "CANCELADO_POR_CLIENTE"]

    # LQ-01: solo cuentan los pagos verificados
    verified = []
    for order in orders:
        if order.payment_status == "VERIFICADO":
            verified.append(order)
        else:
            settled[order.order_id] = SettledOrder(  # BS-10: el saldo usado vuelve
                order.order_id, "CANCELADO", order.total, returned_to_balance=order.paid_with_balance,
            )

    # LQ-02: mínimo por grupo de zonas
    def group_of(order: Order) -> str:
        return store.zones[order.zone_id].group_id

    per_group = Counter(group_of(order) for order in verified)
    attended: dict[int, Order] = {}
    for order in verified:
        if per_group[group_of(order)] < MIN_ORDERS_PER_GROUP:
            settled[order.order_id] = SettledOrder(  # BS-09: externo al medio de pago, saldo a saldo
                order.order_id, "NO_ATENDIDO", order.total,
                refund_amount=order.paid_external, refund_destination="MEDIO_DE_PAGO",
                returned_to_balance=order.paid_with_balance,
            )
        else:
            attended[order.order_id] = order

    missing_qty = _missing_by_order(missing, attended)

    # LQ-03 y LQ-04: tramo según lo pedido entre todos los pedidos atendidos
    totals: dict[str, Decimal] = {}
    for order in attended.values():
        for line in order.lines:
            totals[line.product_id] = totals.get(line.product_id, ZERO) + line.quantity

    catalog = store.catalog_for(cycle)  # CT-10
    products: dict[str, ProductSummary] = {}
    for product_id, total_quantity in totals.items():
        product = catalog[product_id]
        tier = product.tier_for(total_quantity)
        price = min(product.price_with_commission(tier.base_price), product.max_unit_price())
        products[product_id] = ProductSummary(product_id, total_quantity, tier.min_quantity, price)

    # LQ-05: envío repartido por zona, con tope
    per_zone = Counter(order.zone_id for order in attended.values())
    fee_by_zone = {
        zone_id: min(store.zones[zone_id].stop_cost / count, MAX_DELIVERY_FEE)
        for zone_id, count in per_zone.items()
    }

    # LQ-06..LQ-08: monto final y saldo a favor
    for order in attended.values():
        lines = []
        amount = fee_by_zone[order.zone_id]
        for line in order.lines:
            lost = missing_qty.get((order.order_id, line.product_id), ZERO)
            delivered = line.quantity - lost
            price = products[line.product_id].final_unit_price
            amount += price * delivered
            lines.append(SettledLine(line.product_id, line.quantity, lost, delivered, price))
        final_amount = floor_cents(amount)
        settled[order.order_id] = SettledOrder(
            order.order_id, "LIQUIDADO", order.total, lines,
            delivery_fee=fee_by_zone[order.zone_id],
            final_amount=final_amount,
            refund_amount=order.total - final_amount,
            refund_destination="SALDO",
        )

    # Recién aquí, con todo validado, se aplican los efectos (estados, billetera, reembolsos).
    for result in settled.values():
        order = store.orders[result.order_id]
        order.status = result.status
        reference = f"pedido {order.order_id}"
        if result.status == "LIQUIDADO":
            wallet.credit(store, order.customer_id, result.refund_amount, "ABONO_LIQUIDACION", at, reference)
        wallet.credit(store, order.customer_id, result.returned_to_balance, "DEVOLUCION_A_SALDO", at, reference)
        if result.status == "NO_ATENDIDO" and result.refund_amount > 0:
            wallet.add_refund(store, order.customer_id, result.refund_amount, "ZONA_NO_ATENDIDA", at)
    store.settled_cycles.add(cycle)

    # LQ-09: resumen del ciclo
    total_credited = sum((o.refund_amount for o in settled.values() if o.status == "LIQUIDADO"), ZERO)
    total_refunded = sum((o.refund_amount for o in settled.values() if o.status == "NO_ATENDIDO"), ZERO)
    ordered_ids = sorted(settled)
    result = CycleSettlement(
        cycle,
        {order_id: settled[order_id] for order_id in ordered_ids},
        products,
        total_credited,
        total_refunded,
    )
    store.settlements[cycle] = result  # RV-03: los reclamos usan el precio final
    return result
