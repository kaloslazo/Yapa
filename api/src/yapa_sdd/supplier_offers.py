"""Lista semanal propuesta por el proveedor y su pedido consolidado (iteración 54).

Spec: docs/desarrollo/54-proveedores-y-transportistas.md. El proveedor propone; publica el administrador (RN-16).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from . import cycle as cycles
from . import partners
from .catalog import _check_admin, _check_product, parse_catalog, publish_catalog
from .domain import BusinessRuleError, Product
from .fulfillment import is_attended
from .store import InMemoryStore


@dataclass(frozen=True)
class SupplierOffer:
    cycle: str
    supplier_id: str
    products: tuple[Product, ...]
    status: str  # PENDIENTE, APROBADA o RECHAZADA
    sent_by: str
    sent_at: datetime
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    reason: str = ""


def submit_offer(store: InMemoryStore, cycle: str, text: str, *, by: str, now: datetime) -> SupplierOffer:
    """PV-01..PV-03, S-284 y S-285."""
    account = partners.active(store, by, partners.SUPPLIER)
    if account is None:
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo un proveedor aliado puede mandar su lista.")
    cycles.check_cycle_id(cycle)
    if cycles.to_lima(now) >= cycles.opens_at(cycle):  # PV-01, como CT-08
        raise BusinessRuleError("CATALOG_LOCKED", "Ese ciclo ya abrió; manda tu lista para la semana que viene.")
    current = store.catalog_for(cycle)
    checked: dict[str, Product] = {}
    for product in parse_catalog(text):
        if product.supplier_id not in (None, account.supplier_id):  # PV-03
            raise BusinessRuleError("FOREIGN_SUPPLIER", f"{product.name}: la lista solo puede traer tus productos.")
        product = replace(product, supplier_id=account.supplier_id)
        owner = current.get(product.product_id) or store.products.get(product.product_id)
        if owner is not None and owner.supplier_id != account.supplier_id:
            raise BusinessRuleError("FOREIGN_PRODUCT", f"{product.name}: ese código es de otro proveedor.")
        _check_product(store, product, checked)  # PV-02
        checked[product.product_id] = product
    offer = SupplierOffer(cycle, account.supplier_id, tuple(checked.values()), "PENDIENTE", by, now)
    store.supplier_offers[(cycle, account.supplier_id)] = offer
    return offer


def _pending(store: InMemoryStore, cycle: str, supplier_id: str, by: str) -> SupplierOffer:
    _check_admin(store, by)
    offer = store.supplier_offers.get((cycle, supplier_id))
    if offer is None:
        raise BusinessRuleError("OFFER_NOT_FOUND", "Ese proveedor no mandó lista para ese ciclo.")
    if offer.status != "PENDIENTE":
        raise BusinessRuleError("OFFER_NOT_PENDING", "Esa lista ya fue revisada.")
    return offer


def approve_offer(store: InMemoryStore, cycle: str, supplier_id: str, *, by: str, now: datetime) -> SupplierOffer:
    """PV-04, S-286: sus productos se reemplazan; los de los demás quedan. Todo o nada (CT-07)."""
    offer = _pending(store, cycle, supplier_id, by)
    others = [p for p in store.catalog_for(cycle).values() if p.supplier_id != supplier_id]
    publish_catalog(store, cycle, others + list(offer.products), by=by, now=now)
    store.supplier_offers[(cycle, supplier_id)] = replace(offer, status="APROBADA", reviewed_by=by, reviewed_at=now)
    return store.supplier_offers[(cycle, supplier_id)]


def reject_offer(store: InMemoryStore, cycle: str, supplier_id: str, reason: str, *, by: str,
                 now: datetime) -> SupplierOffer:
    """PV-05, S-287."""
    offer = _pending(store, cycle, supplier_id, by)
    reason = (reason or "").strip()
    if not reason:
        raise BusinessRuleError("REASON_REQUIRED", "Escribe por qué se rechaza, para que el proveedor lo corrija.")
    store.supplier_offers[(cycle, supplier_id)] = replace(offer, status="RECHAZADA", reviewed_by=by,
                                                          reviewed_at=now, reason=reason)
    return store.supplier_offers[(cycle, supplier_id)]


def supplier_order(store: InMemoryStore, cycle: str, supplier_id: str, now: datetime) -> dict:
    """PV-06, S-288: totales de sus productos en los pedidos que se atienden, a su precio del tramo alcanzado."""
    catalog = store.catalog_for(cycle)
    totals: dict[str, Decimal] = {}
    for order in store.orders_in_cycle(cycle):
        if not is_attended(store, order):
            continue
        for line in order.lines:
            product = catalog.get(line.product_id)
            if product is not None and product.supplier_id == supplier_id:
                totals[line.product_id] = totals.get(line.product_id, Decimal("0")) + line.quantity
    lines = []
    for product_id in sorted(totals):
        product, quantity = catalog[product_id], totals[product_id]
        tier = product.tier_for(quantity)
        lines.append({"producto": product_id, "nombre": product.name, "unidad": product.unit, "cantidad": quantity,
                      "desde": tier.min_quantity, "precio": tier.base_price, "monto": quantity * tier.base_price})
    return {"ciclo": cycle, "parcial": cycles.to_lima(now) < cycles.closes_at(cycle), "lineas": lines,
            "total": sum((line["monto"] for line in lines), Decimal("0"))}
