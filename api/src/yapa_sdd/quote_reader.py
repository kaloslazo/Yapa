"""La cotización del proveedor leída con IA (iteración 69): foto o texto -> borrador de su lista.

Spec: docs/desarrollo/69-lista-del-proveedor-con-ia.md. Solo llena el borrador del editor: nada se guarda aquí;
la lista se manda y se aprueba como siempre (PV-01..PV-03).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation

from . import cycle as cycles
from . import partners
from .domain import BusinessRuleError, Product
from .ia import AIClient
from .store import InMemoryStore

DAILY_LIMIT = 20  # S-350
MAX_PHOTO = 8 * 1024 * 1024  # LP-04, como S-151
MIN_PRICE, MAX_PRICE = Decimal("0.01"), Decimal("1000")  # S-349
PRICE = re.compile(r"(?:s/\.?|\ba)\s*(\d+(?:[.,]\d{1,2})?)", re.I)  # S-346
QUANTITY = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kilos?|unidades|unid|und|u)\b", re.I)
UNIT_WORDS = ("unidad", "unidades", "u", "und", "unid")

SYSTEM = (
    "Lees la cotización de un proveedor mayorista de Lima (foto de pizarra, cuaderno o lista, o un mensaje). "
    "Productos que el proveedor ya vende (codigo|nombre|unidad): {catalog}. Usa ese código si es el mismo producto; "
    "si es un producto nuevo, deja el código vacío. Responde SOLO un objeto JSON con la forma "
    '{{"filas":[{{"codigo":"","nombre":"","unidad":"kg o unidad","maximo":numero o null,'
    '"tramos":[{{"desde":numero,"precio":numero}}]}}]}}. "maximo" es la cantidad disponible si está escrita. '
    "Cada tramo es un precio por kg o por unidad desde cierta cantidad; el primero es desde 0. "
    "No inventes precios ni cantidades que no estén escritos."
)


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def code_for(name: str) -> str:
    """S-348: código hecho con el nombre."""
    return re.sub(r"[^A-Z0-9]+", "-", _plain(name).upper()).strip("-")[:40]


def _number(value) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value).replace(",", ".").strip())
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _photo_type(content: bytes) -> str:
    """LP-04: los mismos tipos que el resto de las fotos."""
    if len(content) > MAX_PHOTO:
        raise BusinessRuleError("PHOTO_TOO_LARGE", "La foto pesa más de 8 MB.")
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    raise BusinessRuleError("INVALID_PHOTO", "Usa una foto JPG, PNG o WebP.")


def _count_use(store: InMemoryStore, user: str, now: datetime) -> None:
    """S-350."""
    key = f"proveedor:{user}:{cycles.to_lima(now).date().isoformat()}"
    if store.ia_usage.get(key, 0) >= DAILY_LIMIT:
        raise BusinessRuleError("IA_LIMIT", f"Ya leíste {DAILY_LIMIT} cotizaciones hoy. Mañana puedes leer más.")
    store.ia_usage[key] = store.ia_usage.get(key, 0) + 1


def _products(store: InMemoryStore, supplier_id: str, now: datetime) -> tuple[dict[str, Product], set[str]]:
    """Lo del proveedor (en la lista de la semana que viene o en la base) y los códigos de otros proveedores."""
    upcoming = store.catalog_for(cycles.add_weeks(cycles.cycle_id(now), 1))
    everything = {**store.products, **upcoming}
    own = {code: p for code, p in everything.items() if p.supplier_id == supplier_id}
    return own, {code for code, p in everything.items() if p.supplier_id not in (None, supplier_id)}


def _by_rules(text: str, own: dict[str, Product]) -> list[dict]:
    """S-346: renglón con el nombre de un producto -> precio y cantidad; "desde" -> tramo del anterior."""
    names = sorted(own.values(), key=lambda p: len(p.name), reverse=True)
    rows: list[dict] = []
    for line in text.splitlines():
        plain = _plain(line).strip()
        price = PRICE.search(plain)
        if not plain or not price:
            continue
        if plain.startswith("desde") and rows:
            start = re.search(r"\d+(?:[.,]\d+)?", plain)
            rows[-1]["tramos"].append({"desde": start.group(0), "precio": price.group(1)})
            continue
        product = next((p for p in names if _plain(p.name) in plain), None)
        if product is None:
            continue
        rest = plain[:price.start()] + plain[price.end():]
        quantity = QUANTITY.search(rest)
        rows.append({"codigo": product.product_id, "nombre": product.name, "unidad": product.unit,
                     "maximo": quantity.group(1) if quantity else None,
                     "tramos": [{"desde": "0", "precio": price.group(1)}]})
    return rows


def _clean(raw: dict, own: dict[str, Product], foreign: set[str], warnings: list[str]) -> dict | None:
    """S-347..S-349."""
    name = str(raw.get("nombre") or "").strip()[:80]
    code = str(raw.get("codigo") or "").strip().upper()
    if code not in own:
        code = next((c for c, p in own.items() if _plain(p.name) == _plain(name)), "") or code or code_for(name)
    label = name or code
    if not code:
        return None
    if code in foreign:
        warnings.append(f"{label}: es un producto de otro proveedor, no se agregó.")
        return None
    tiers: dict[Decimal, Decimal] = {}
    for tier in raw.get("tramos") or []:
        start, price = _number((tier or {}).get("desde")), _number((tier or {}).get("precio"))
        if start is not None and start >= 0 and price is not None and MIN_PRICE <= price <= MAX_PRICE:
            tiers.setdefault(start, price)
    if not tiers:
        warnings.append(f"{label}: no se leyó un precio válido, revísalo a mano.")
        return None
    ordered = sorted(tiers.items())
    ordered[0] = (Decimal("0"), ordered[0][1])
    maximum = _number(raw.get("maximo"))
    maximum = maximum if maximum is not None and maximum >= 0 else None
    known = own.get(code)
    if known is not None:
        category, unit, step = known.category, known.unit, known.step
        maximum = known.max_available if maximum is None else maximum
    else:
        unit = "unidad" if _plain(str(raw.get("unidad") or "")).strip() in UNIT_WORDS else "kg"
        category, step = ("FRESCOS" if unit == "kg" else "LIMPIEZA"), Decimal("1")
        maximum = Decimal("0") if maximum is None else maximum
    return {"codigo": code, "nombre": name or (known.name if known else code), "categoria": category, "unidad": unit,
            "paso": step, "maximo": maximum, "tramos": [{"desde": d, "precio": p} for d, p in ordered]}


def read_quote(store: InMemoryStore, ai: AIClient | None, user: str, *, text: str = "", photo=None,
               now: datetime) -> dict:
    """LP-01..LP-06."""
    account = partners.active(store, user, partners.SUPPLIER)
    if account is None:  # LP-07
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo un proveedor aliado puede leer su cotización.")
    text = str(text or "").strip()[:4000]
    content = photo[1] if photo and photo[1] else b""
    if not text and not content:
        raise BusinessRuleError("LIST_REQUIRED", "Pega el mensaje o elige la foto de tu cotización.")
    image = (_photo_type(content), content) if content else None
    if image and ai is None:  # LP-03
        raise BusinessRuleError("IA_DISABLED", "La lectura de fotos con IA no está activada en este servidor.")
    _count_use(store, user, now)
    own, foreign = _products(store, account.supplier_id, now)
    warnings: list[str] = []
    rows, source = None, "ia"
    if ai is not None:
        catalog = "; ".join(f"{p.product_id}|{p.name}|{p.unit}" for p in own.values())
        try:
            answer, _ = ai.ask_json(SYSTEM.format(catalog=catalog), text or "Lee esta cotización.", image)
            rows = answer.get("filas") if isinstance(answer.get("filas"), list) else None
        except BusinessRuleError:
            rows = None
        if rows is None and image:  # LP-05
            raise BusinessRuleError("IA_UNAVAILABLE", "No pudimos leer la foto ahora. Intenta en un rato o pega el texto.")
        if rows is None:
            warnings.append("La IA no respondió: leímos el texto con reglas simples. Revisa cada producto.")
    if rows is None:
        rows, source = _by_rules(text, own), "reglas"
    cleaned, seen = [], set()
    for raw in rows:
        row = _clean(raw if isinstance(raw, dict) else {}, own, foreign, warnings)
        if row is not None and row["codigo"] not in seen:
            seen.add(row["codigo"])
            cleaned.append(row)
    return {"filas": cleaned, "nuevos": [r["codigo"] for r in cleaned if r["codigo"] not in own],
            "avisos": warnings, "fuente": source}
