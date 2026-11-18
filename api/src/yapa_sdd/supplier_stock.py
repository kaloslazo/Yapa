"""Iteración 72: el stock que el proveedor confirma con una foto de cada carga.

Va aparte del catálogo publicado y de las reservas: solo llena la cantidad disponible del borrador de su lista.
"""
import hashlib
from decimal import Decimal, InvalidOperation, ROUND_FLOOR

from . import cycle, partners
from .domain import BusinessRuleError

MAX_PHOTO_BYTES = 8 * 1024 * 1024
MAX_ROWS = 30
MAX_UNITS = 300
MAX_WEIGHT = Decimal("100000")


def _supplier(store, user: str) -> str:
    account = partners.active(store, user, partners.SUPPLIER)
    if not account:
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo el proveedor puede confirmar su stock.")
    return account.supplier_id


def snapshot(store, user: str, cycle_id: str) -> dict:
    """ST72-1: lo confirmado de este proveedor en esa semana, sumado por producto."""
    supplier = _supplier(store, user)
    cycle.check_cycle_id(cycle_id)
    totals = {}
    for (owner, week, _photo), batch in store.supplier_stock_batches.items():
        if (owner, week) != (supplier, cycle_id):
            continue
        for row in batch["filas"]:
            total = totals.setdefault(row["id"], {"unidades": 0, "cantidad": Decimal("0")})
            total["unidades"] += row["unidades"]
            total["cantidad"] += row["cantidad"]
    products = []
    catalog = store.catalog_for(cycle_id)
    for code, total in sorted(totals.items()):
        product = catalog.get(code)
        if product is None:
            continue
        # S-363: lo vendible se redondea hacia abajo al paso del producto
        available = (total["cantidad"] / product.step).to_integral_value(rounding=ROUND_FLOOR) * product.step
        products.append({"id": code, "nombre": product.name, "unidad": product.unit, "unidades": total["unidades"],
                         "cantidad": format(total["cantidad"].normalize(), "f"),
                         "disponible": format(available.normalize(), "f")})
    return {"ciclo": cycle_id, "productos": products}


def _check_photo(upload) -> bytes:
    if not upload or not upload[1]:
        raise BusinessRuleError("PHOTO_REQUIRED", "Falta la foto de esta carga.")
    content = upload[1]
    if len(content) > MAX_PHOTO_BYTES:
        raise BusinessRuleError("PHOTO_TOO_LARGE", "La foto pesa más de 8 MB.")
    is_jpeg = content.startswith(b"\xff\xd8\xff")
    is_png = content.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        raise BusinessRuleError("INVALID_PHOTO", "Usa una foto JPG, PNG o WebP.")
    return content


def _weight(row: dict, product) -> Decimal:
    """S-362: en kg manda el peso medido; las unidades que se ven en la foto nunca se pasan a kilos."""
    try:
        quantity = Decimal(str(row.get("peso")))
    except InvalidOperation:
        quantity = Decimal("NaN")
    if not quantity.is_finite() or not 0 < quantity <= MAX_WEIGHT:
        raise BusinessRuleError("WEIGHT_REQUIRED",
                                f"Ingresa el peso medido en kg de {product.name}; la foto solo cuenta unidades.")
    return quantity


def _clean_rows(store, supplier: str, cycle_id: str, rows) -> list[dict]:
    """ST72-3: se revisa toda la carga antes de guardar nada."""
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
        raise BusinessRuleError("INVALID_STOCK_ITEM", "Confirma entre 1 y 30 filas de productos.")
    catalog = store.catalog_for(cycle_id)
    clean = []
    for row in rows:
        product = catalog.get(row.get("id")) if isinstance(row, dict) else None
        units = row.get("unidades") if isinstance(row, dict) else None
        if not product or product.supplier_id != supplier or not product.active:
            raise BusinessRuleError("INVALID_STOCK_ITEM", "Elige productos de tu lista y unidades enteras entre 1 y 300.")
        if type(units) is not int or not 1 <= units <= MAX_UNITS:
            raise BusinessRuleError("INVALID_STOCK_ITEM", "Elige productos de tu lista y unidades enteras entre 1 y 300.")
        quantity = _weight(row, product) if product.unit == "kg" else Decimal(units)
        clean.append({"id": product.product_id, "unidades": units, "cantidad": quantity})
    return clean


def confirm(store, user: str, cycle_id: str, rows, upload, now) -> dict:
    """ST72-1..ST72-3: suma una carga a la semana de la propuesta; la misma foto no se suma dos veces (S-361)."""
    supplier = _supplier(store, user)
    if cycle_id != cycle.add_weeks(cycle.cycle_id(now), 1):
        raise BusinessRuleError("INVALID_STOCK_CYCLE", "Confirma stock para la próxima semana de tu propuesta.")
    content = _check_photo(upload)
    clean = _clean_rows(store, supplier, cycle_id, rows)
    # el bloqueo de la API hace que esta parte no se cruce con otra confirmación
    key = (supplier, cycle_id, hashlib.sha256(content).hexdigest())
    previous = store.supplier_stock_batches.get(key)
    if previous is not None and previous["filas"] != clean:
        raise BusinessRuleError("STOCK_ALREADY_CONFIRMED", "Esta foto ya fue confirmada con otro conteo; no se sumó de nuevo.")
    if previous is None:
        store.supplier_stock_batches[key] = {"filas": clean, "por": user, "hora": now}
    return snapshot(store, user, cycle_id) | {"repetida": previous is not None}
