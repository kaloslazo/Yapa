"""Catálogo semanal del proveedor aliado (iteración 6, CUN-01).

Spec: docs/desarrollo/06-catalogo-semanal.md.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from . import cycle as cycles
from .domain import COMMISSION, BusinessRuleError, PriceTier, Product
from .store import InMemoryStore


def _check_admin(store: InMemoryStore, by: str) -> None:
    if by not in store.admins:  # CT-01, RN-16
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo el administrador de Yapa puede cambiar el catálogo.")


def _check_tiers(product: Product) -> None:
    """S-34: empieza en 0, cantidades crecientes y precios positivos y estrictamente decrecientes."""
    tiers = product.tiers
    valid = bool(tiers) and tiers[0].min_quantity == 0 and all(tier.base_price > 0 for tier in tiers)
    for previous, current in zip(tiers, tiers[1:]):
        if current.min_quantity <= previous.min_quantity or current.base_price >= previous.base_price:
            valid = False
    if not valid:
        raise BusinessRuleError("INVALID_TIERS", f"{product.name}: los precios por tramo no son válidos.")


def _check_product(store: InMemoryStore, product: Product, published: dict[str, Product]) -> None:
    supplier = store.suppliers.get(product.supplier_id)
    if supplier is None or not supplier.allied:  # CT-02
        raise BusinessRuleError("SUPPLIER_NOT_ALLIED", f"{product.name}: el proveedor no es aliado de Yapa.")
    _check_tiers(product)  # CT-03
    if product.step <= 0 or product.max_available <= 0 or product.max_available % product.step != 0:  # CT-04, S-120
        raise BusinessRuleError("INVALID_STOCK", f"{product.name}: la cantidad máxima no es válida.")
    if product.product_id in published:  # CT-05
        raise BusinessRuleError("DUPLICATE_PRODUCT", f"{product.name} aparece más de una vez.")
    if product.category not in COMMISSION:  # CT-06
        raise BusinessRuleError("INVALID_CATEGORY", f"{product.name}: la categoría no está en el piloto.")


def publish_catalog(store: InMemoryStore, cycle: str, products: Iterable[Product], *, by: str,
                    now: datetime) -> dict[str, Product]:
    _check_admin(store, by)  # CT-01
    if cycles.to_lima(now) >= cycles.opens_at(cycle):  # CT-08, S-33
        raise BusinessRuleError("CATALOG_LOCKED", "El ciclo ya abrió; su catálogo ya no puede cambiar.")
    catalog: dict[str, Product] = {}
    for product in products:
        _check_product(store, product, catalog)
        catalog[product.product_id] = product
    store.catalogs[cycle] = catalog  # CT-07: se guarda solo si todos los productos pasaron
    return catalog


def deactivate_product(store: InMemoryStore, cycle: str, product_id: str, *, by: str) -> Product:
    """CT-09, S-36: no acepta pedidos nuevos; los ya registrados se liquidan normal."""
    _check_admin(store, by)
    catalog = store.catalogs.get(cycle)
    if catalog is None:  # S-118: el ciclo usa el catálogo base; se desactiva en una copia
        catalog = dict(store.products)
    if product_id not in catalog:
        raise BusinessRuleError("PRODUCT_NOT_AVAILABLE", f"{product_id} no está en el catálogo del ciclo.")
    store.catalogs[cycle] = catalog
    catalog[product_id] = replace(catalog[product_id], active=False)
    return catalog[product_id]


COLUMNS = "codigo,nombre,categoria,unidad,paso,maximo,proveedor,desde1,precio1,desde2,precio2"
NUMBER = re.compile(r"\d+(\.\d+)?")


def _format_error(line_number: int, detail: str) -> BusinessRuleError:
    return BusinessRuleError("INVALID_CATALOG_FORMAT", f"La lista tiene un error en la línea {line_number}: {detail}.")


def _number(text: str, line_number: int) -> Decimal:
    text = text.strip()
    if not NUMBER.fullmatch(text):
        raise _format_error(line_number, f"'{text}' no es un número con punto decimal")
    return Decimal(text)


def parse_catalog(text: str) -> list[Product]:
    """CW-02, S-116: una línea por producto, separada por comas."""
    products = []
    for line_number, line in enumerate((text or "").splitlines(), start=1):
        if not line.strip() or line.strip().lower().startswith("codigo"):
            continue
        cells = [cell.strip() for cell in line.split(",")]
        if len(cells) < 9 or len(cells[7:]) % 2 != 0:
            raise _format_error(line_number, "faltan columnas o un tramo no tiene precio")
        product_id, name, category, unit = cells[:4]
        if not product_id or not name:
            raise _format_error(line_number, "falta el código o el nombre")
        numbers = [_number(cell, line_number) for cell in cells[7:]]
        tiers = tuple(PriceTier(numbers[i], numbers[i + 1]) for i in range(0, len(numbers), 2))
        products.append(Product(product_id, name, category, unit, _number(cells[4], line_number),
                                _number(cells[5], line_number), tiers, supplier_id=cells[6] or None))
    if not products:
        raise BusinessRuleError("INVALID_CATALOG_FORMAT", "La lista está vacía.")
    return products


def export_catalog(products: Iterable[Product]) -> str:
    """S-117: los productos activos en el mismo formato que se publica."""
    lines = [COLUMNS]
    for p in products:
        if p.active:
            tiers = [str(value) for tier in p.tiers for value in (tier.min_quantity, tier.base_price)]
            lines.append(",".join([p.product_id, p.name, p.category, p.unit, str(p.step), str(p.max_available),
                                   p.supplier_id or ""] + tiers))
    return "\n".join(lines)
