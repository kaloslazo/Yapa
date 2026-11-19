"""IA de Yapa: "Arma mi canasta" (iteración 60) y ayuda para atención (iteración 61).

Specs: docs/desarrollo/60-arma-mi-canasta-ia.md y 61-atencion-con-ia.md.
La IA solo sugiere: los precios, los pasos, los topes y el mínimo los sigue aplicando el motor, y nada cambia de estado.
Proveedores con el formato "chat completions" de OpenAI: Groq (principal) y GitHub Models (respaldo), S-314.
Para fotos, primero Claude en Amazon Bedrock si está configurado (iteración 78, `bedrock.py`).
Solo biblioteca estándar, como el resto del motor.
"""

from __future__ import annotations

import base64
import json
import math
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Callable

from . import bedrock
from . import cycle as cycles
from . import partners
from .domain import MAX_QUANTITY, MIN_SUBTOTAL, BusinessRuleError, ceil_cents
from .fulfillment import check_role
from .store import InMemoryStore


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GITHUB_URL = "https://models.github.ai/inference/chat/completions"
TIMEOUT = 15  # S-314: segundos por proveedor
DAILY_LIMIT = 10  # S-315: sugerencias por vecino al día
MAX_PRODUCTS = 12  # S-317
CATEGORIES = ("FALTANTE", "DANADO", "ENTREGA", "PAGO", "TRATO", "OTRO")  # S-318
PRIORITIES = ("ALTA", "MEDIA", "BAJA")


class AIError(Exception):
    """Un proveedor no respondió bien (error HTTP, límite, tiempo o respuesta ilegible)."""


@dataclass(frozen=True)
class Provider:
    name: str
    url: str
    key: str
    model: str
    vision_model: str = ""  # S-345: el modelo que lee fotos; vacío, el mismo de texto
    kind: str = "openai"  # "bedrock": solo fotos, con la API Converse y firma de AWS (iteración 78)
    secret: str = ""  # Bedrock: la clave secreta del usuario IAM (S-383)
    region: str = ""
    token: str = ""
    account: str = ""  # S-384: la cuenta de AWS esperada; vacío, no se revisa


def http_post(url: str, headers: dict, body: dict | bytes, timeout: float) -> dict:
    data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")  # bytes: ya firmados (Bedrock)
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (URL fija de S-314)
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        raise AIError(str(error)) from error


class AIClient:
    def __init__(self, providers: list[Provider], post: Callable = http_post, timeout: float = TIMEOUT):
        self.providers = providers
        self.post = post
        self.timeout = timeout

    def ask_json(self, system: str, user: str, image: tuple[str, bytes] | None = None,
                 max_tokens: int | None = None) -> tuple[dict, str]:
        """IA-04: el principal y, si falla, el respaldo. Devuelve el JSON y el nombre del proveedor que respondió.
        Con `image` (tipo y bytes), la foto va como image_url en base64 al modelo de visión (S-345)."""
        content = user
        if image is not None:
            encoded = base64.b64encode(image[1]).decode("ascii")
            content = [{"type": "text", "text": user},
                       {"type": "image_url", "image_url": {"url": f"data:{image[0]};base64,{encoded}"}}]
        for provider in self.providers:
            if provider.kind == "bedrock":
                if image is None:  # BR-04: el texto no va a Bedrock
                    continue
                try:  # BR-02, BR-03
                    text = bedrock.converse(provider, system, user, image, max_tokens, self.post, self.timeout)
                    return _json_object(text), provider.name
                except (AIError, KeyError, IndexError, TypeError, ValueError, StopIteration):
                    continue
            model = (provider.vision_model or provider.model) if image is not None else provider.model
            body = {"model": model, "temperature": 0.2, "response_format": {"type": "json_object"},
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}]}
            if max_tokens:
                body["max_tokens"] = max_tokens  # S-352: respuestas cortas gastan menos cupo
            if model.startswith("openai/gpt-oss"):
                body["reasoning_effort"] = "low"  # S-355: si razona mucho se queda sin tokens para responder
            headers = {"Authorization": f"Bearer {provider.key}", "Content-Type": "application/json",
                       "User-Agent": "yapa"}
            try:
                data = self.post(provider.url, headers, body, self.timeout)
                return _json_object(data["choices"][0]["message"]["content"]), provider.name
            except (AIError, KeyError, IndexError, TypeError, ValueError):
                continue
        raise BusinessRuleError("IA_UNAVAILABLE", "La ayuda con IA no está disponible ahora. Intenta en un rato.")


def from_env(env) -> AIClient | None:
    """S-314: Groq primero y GitHub Models de respaldo; sin ninguna clave, no hay IA.
    S-381 y S-383: con las claves propias de Bedrock, las fotos van primero a Bedrock."""
    providers = []
    key_id = (env.get("YAPA_BEDROCK_CLAVE_ID") or "").strip()
    secret = (env.get("YAPA_BEDROCK_CLAVE_SECRETA") or "").strip()
    if key_id and secret:
        region = (env.get("YAPA_BEDROCK_REGION") or bedrock.DEFAULT_REGION).strip()
        providers.append(Provider("bedrock", "", key_id, (env.get("YAPA_BEDROCK_MODELO") or bedrock.DEFAULT_MODEL).strip(),
                                  kind="bedrock", secret=secret, region=region,
                                  token=(env.get("YAPA_BEDROCK_TOKEN_SESION") or "").strip(),
                                  account=(env.get("YAPA_BEDROCK_CUENTA") or "").strip()))
    if (env.get("YAPA_GROQ_CLAVE") or "").strip():
        providers.append(Provider("groq", GROQ_URL, env["YAPA_GROQ_CLAVE"].strip(),
                                  (env.get("YAPA_GROQ_MODELO") or "openai/gpt-oss-120b").strip(),
                                  (env.get("YAPA_GROQ_MODELO_VISION") or "qwen/qwen3.8-27b").strip()))
    if (env.get("YAPA_GITHUB_MODELS_CLAVE") or "").strip():
        providers.append(Provider("github", GITHUB_URL, env["YAPA_GITHUB_MODELS_CLAVE"].strip(),
                                  (env.get("YAPA_GITHUB_MODELS_MODELO") or "openai/gpt-4o-mini").strip(),
                                  (env.get("YAPA_GITHUB_MODELS_MODELO_VISION") or "openai/gpt-4o-mini").strip()))
    return AIClient(providers) if providers else None


def _json_object(text: str) -> dict:
    """Acepta el JSON solo o rodeado de texto; tiene que ser un objeto."""
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        found = re.search(r"\{.*\}", text or "", re.S)
        if not found:
            raise ValueError("sin JSON")
        value = json.loads(found.group(0))
    if not isinstance(value, dict):
        raise ValueError("no es un objeto")
    return value


def _require(ai: AIClient | None) -> AIClient:
    if ai is None:  # IA-01
        raise BusinessRuleError("IA_DISABLED", "La ayuda con IA no está activada en este servidor.")
    return ai


# --- Arma mi canasta (iteración 60) ---

BASKET_SYSTEM = (
    "Eres el asistente de compras de Yapa, una compra grupal de frescos y limpieza en Lima. Con lo que el vecino "
    "escribe, propones una canasta para la semana usando SOLO los productos del catálogo que te paso, con su código "
    "exacto y cantidades en la unidad indicada. Responde únicamente un objeto JSON con la forma "
    '{"lineas":[{"id":"CODIGO","cantidad":numero}],"comentario":"una frase corta en español"}.'
)


def _count_use(store: InMemoryStore, customer_id: int, now: datetime) -> None:
    """IA-03, S-315: hasta 10 sugerencias por vecino y por día de Lima."""
    key = f"{customer_id}:{cycles.to_lima(now).date().isoformat()}"
    if store.ia_usage.get(key, 0) >= DAILY_LIMIT:
        raise BusinessRuleError("IA_LIMIT", f"Ya usaste las {DAILY_LIMIT} sugerencias de hoy. Mañana puedes pedir más.")
    store.ia_usage[key] = store.ia_usage.get(key, 0) + 1


def suggest_basket(store: InMemoryStore, ai: AIClient | None, customer_id: int, text, now: datetime) -> dict:
    ai = _require(ai)
    wish = str(text or "").strip()
    if not 3 <= len(wish) <= 300:  # IA-02
        raise BusinessRuleError("INVALID_INPUT", "Cuéntanos en 3 a 300 caracteres qué vas a cocinar.")
    cycle_id = cycles.cycle_id(now)
    catalog = {p.product_id: p for p in store.catalog_for(cycle_id).values() if p.active}
    lines = [f"{p.product_id} | {p.name} | por {p.unit} | paso {p.step} | hasta {MAX_QUANTITY[p.unit]} | "
             f"S/ {p.max_unit_price():.2f}" for p in catalog.values()]
    user = "Catálogo de esta semana (código | nombre | unidad | paso | tope | precio máximo):\n" + "\n".join(lines) + \
           f"\n\nLo que escribió el vecino: {wish}"  # IA-07, S-316: sin datos del vecino
    _count_use(store, customer_id, now)
    answer, provider = ai.ask_json(BASKET_SYSTEM, user)

    wanted: dict[str, Decimal] = {}  # S-317: solo del catálogo, repetidos sumados, hasta 12 productos
    for item in answer.get("lineas") or []:
        if not isinstance(item, dict):
            continue
        product = catalog.get(str(item.get("id", "")).strip().upper())
        try:
            quantity = Decimal(str(item.get("cantidad")))
        except (InvalidOperation, ValueError):
            continue
        if product is None or not quantity.is_finite() or quantity <= 0:
            continue
        if product.product_id not in wanted and len(wanted) >= MAX_PRODUCTS:
            continue
        wanted[product.product_id] = wanted.get(product.product_id, Decimal("0")) + quantity
    if not wanted:  # IA-05
        raise BusinessRuleError("IA_EMPTY_SUGGESTION", "No encontramos productos de esta semana para eso. Prueba con otras palabras.")

    result, subtotal = [], Decimal("0")
    for product_id, quantity in wanted.items():
        product = catalog[product_id]
        steps = max(1, math.ceil(quantity / product.step))
        quantity = min(product.step * steps, MAX_QUANTITY[product.unit])  # S-08: tope por línea
        price = product.max_unit_price()  # RP-09: el precio lo pone el motor
        result.append({"id": product_id, "nombre": product.name, "unidad": product.unit, "cantidad": quantity,
                       "precio_max": price, "total": price * quantity})
        subtotal += price * quantity
    comment = str(answer.get("comentario") or "").strip()[:200]
    return {"lineas": result, "subtotal": subtotal, "falta": max(Decimal("0"), ceil_cents(MIN_SUBTOTAL - subtotal)),
            "comentario": comment, "proveedor": provider}


# --- Ayuda para atención (iteración 61) ---

SUPPORT_SYSTEM = (
    "Ayudas al equipo de atención de Yapa, una compra grupal de frescos y limpieza en Lima. Con el caso que te paso, "
    f"elige una categoría ({', '.join(CATEGORIES)}), una prioridad ({', '.join(PRIORITIES)}) y escribe un borrador "
    "de respuesta para el vecino: amable, en español, de hasta 600 caracteres, sin prometer montos ni plazos. "
    'Responde únicamente un objeto JSON: {"categoria":"...","prioridad":"...","borrador":"..."}.'
)


def suggest_support(store: InMemoryStore, ai: AIClient | None, kind: str, record_id, *, by) -> dict:
    check_role(store, by, partners.SUPPORT)  # IA-10
    if kind not in ("reclamo", "incidencia"):  # IA-11
        raise BusinessRuleError("INVALID_INPUT", "Elige un reclamo o una incidencia.")
    try:
        record_id = int(record_id)
    except (TypeError, ValueError):
        raise BusinessRuleError("INVALID_INPUT", "El número no es válido.")
    if kind == "reclamo":
        claim = store.claims.get(record_id)
        if claim is None:
            raise BusinessRuleError("CLAIM_NOT_FOUND", "El reclamo no existe.")
        order = store.orders.get(claim.order_id)
        product = store.catalog_for(order.cycle if order else None).get(claim.product_id)
        case = (f"Reclamo por artículo. Producto: {product.name if product else claim.product_id}. "
                f"Cantidad: {format(claim.quantity.normalize(), 'f')} {product.unit if product else ''}. "
                f"Motivo: {claim.reason}. Estado del reclamo: {claim.status}. "
                f"Estado del pedido: {order.status if order else 'desconocido'}.")
    else:
        incident = store.incidents.get(record_id)
        if incident is None:
            raise BusinessRuleError("INCIDENT_NOT_FOUND", "La incidencia no existe.")
        order = store.orders.get(incident.order_id)
        case = (f"Incidencia de tipo {incident.kind}. Lo que contó el vecino: {incident.description}. "
                f"Estado del pedido: {order.status if order else 'desconocido'}.")  # S-318: sin nombre, celular ni correo
    answer, provider = _require(ai).ask_json(SUPPORT_SYSTEM, case)
    draft = str(answer.get("borrador") or "").strip()[:600]  # S-319
    if not draft:
        raise BusinessRuleError("IA_EMPTY_SUGGESTION", "La IA no propuso una respuesta. Intenta de nuevo.")
    category = str(answer.get("categoria") or "").strip().upper()
    priority = str(answer.get("prioridad") or "").strip().upper()
    return {"categoria": category if category in CATEGORIES else "OTRO",
            "prioridad": priority if priority in PRIORITIES else "MEDIA", "borrador": draft, "proveedor": provider}
