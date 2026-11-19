"""Iteración 77: qué productos de una lista se ven en la foto de una bolsa o de una carga, leído con IA.

La IA (visión de Groq, la misma de la iteración 69) recibe la lista del pedido o de los productos del proveedor y
solo puede responder con esos códigos. Sin IA, con falla o pasado el límite, responde el detector local (YOLO).
"""
from datetime import datetime

from . import cycle as cycles, partners, vision
from .domain import BusinessRuleError
from .ia import AIClient
from .store import InMemoryStore

DAILY_LIMIT = 150  # S-378
MAX_UNITS = 300  # S-380
MAX_OTHERS = 5
MAX_OTHER_TEXT = 40
SYSTEM = (
    "Revisas la foto de una bolsa armada para un pedido de Yapa (compras de vecinos en Lima). Te doy la lista de "
    "productos con su código. Di cuáles de esos productos se ven en la foto y cuántas unidades se ven de cada uno "
    "(piezas o envases, no kilos). Usa solo códigos de la lista. Si un producto de la lista no se ve, no lo pongas. "
    "Si en la foto hay algo que no está en la lista, ponlo en \"otros\" con una o dos palabras. Responde solo JSON: "
    "{\"productos\": [{\"id\": \"CODIGO\", \"unidades\": 3}], \"otros\": [\"...\"]}"
)
KINDS = ("zanahoria", "cebolla", "camote", "limon", "papa", "ajo")  # las mismas palabras que usa la pantalla


def _kind(name: str) -> str:
    plain = name.lower().replace("ó", "o").replace("á", "a").replace("í", "i").replace("é", "e").replace("ú", "u")
    return next((k for k in KINDS if k in plain), "otro")


def _name_of(store: InMemoryStore, product_id: str, cycle_id: str) -> str:
    product = store.catalog_for(cycle_id).get(product_id) or store.products.get(product_id)
    return product.name if product else product_id


def order_products(store: InMemoryStore, order_id: int) -> dict[str, str]:
    """S-375: código y nombre de cada línea del pedido."""
    order = store.orders.get(order_id)
    if order is None:  # VB-04
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    return {line.product_id: _name_of(store, line.product_id, order.cycle) for line in order.lines}


def supplier_products(store: InMemoryStore, user: str, now: datetime) -> dict[str, str]:
    """S-376: los productos del proveedor para la semana que viene (o los de la base, si aún no hay lista)."""
    account = partners.active(store, user, partners.SUPPLIER)
    if account is None:
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo el proveedor puede revisar su carga.")
    upcoming = store.catalog_for(cycles.add_weeks(cycles.cycle_id(now), 1))
    everything = {**store.products, **upcoming}
    return {code: p.name for code, p in everything.items() if p.supplier_id == account.supplier_id and p.active}


def _units(value) -> int:
    """S-380: piezas o envases de 1 a 300; lo que no sea un número se vuelve 1."""
    try:
        units = int(value)
    except (TypeError, ValueError):
        return 1
    return min(max(units, 1), MAX_UNITS)


def _clean(answer: dict, products: dict[str, str]) -> tuple[list[dict], list[str]]:
    """VB-02: solo códigos de la lista y sin repetir; "otros" corto."""
    rows, seen = [], set()
    for item in answer.get("productos") or []:
        code = item.get("id") if isinstance(item, dict) else None
        if code not in products or code in seen:
            continue
        seen.add(code)
        rows.append({"codigo": code, "nombre": products[code], "producto": _kind(products[code]),
                     "cantidad": _units(item.get("unidades"))})
    others = [str(o).strip()[:MAX_OTHER_TEXT] for o in answer.get("otros") or [] if str(o).strip()]
    return rows, others[:MAX_OTHERS]


def _photo_type(content: bytes) -> str:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    raise BusinessRuleError("INVALID_PHOTO", "Usa una foto JPG, PNG o WebP válida para analizar.")


def _take_use(store: InMemoryStore, user: str, now: datetime) -> bool:
    """S-378: cuenta la revisión si queda cupo hoy; sin cupo, no se llama a la IA."""
    key = f"bolsa:{user}:{cycles.to_lima(now).date().isoformat()}"
    if store.ia_usage.get(key, 0) >= DAILY_LIMIT:
        return False
    store.ia_usage[key] = store.ia_usage.get(key, 0) + 1
    return True


def _with_ai(ai: AIClient, products: dict[str, str], content: bytes) -> dict | None:
    listing = "\n".join(f"- {code}: {name}" for code, name in products.items())
    try:
        answer, _ = ai.ask_json(SYSTEM, "Productos de la lista:\n" + listing, image=(_photo_type(content), content),
                                max_tokens=400)
    except BusinessRuleError as error:
        if error.code == "INVALID_PHOTO":
            raise
        return None  # VB-03: IA caída
    rows, others = _clean(answer, products)
    return {"fuente": "ia", "productos": rows, "otros": others,
            "aviso": "Sugerencia de la IA con los productos de la lista. Revisa producto y cantidad: no estima peso."}


def read_bag(store: InMemoryStore, ai: AIClient | None, user: str, upload, products: dict[str, str] | None,
             now: datetime) -> dict:
    """VB-01..VB-05: con lista y con IA, la IA; si no, el detector local como antes."""
    if not upload or not upload[1]:
        raise BusinessRuleError("PHOTO_REQUIRED", "Elige una foto para analizar.")
    if len(upload[1]) > 8 * 1024 * 1024:
        raise BusinessRuleError("PHOTO_TOO_LARGE", "La foto pesa más de 8 MB.")
    if products and ai is not None and _take_use(store, user, now):
        result = _with_ai(ai, products, upload[1])
        if result is not None:
            return result
    local = vision.analyze_photo(upload)  # S-377
    return {**local, "fuente": "detector", "otros": []}
