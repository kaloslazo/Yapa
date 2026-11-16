"""Asistente de compra (iteración 70): responde al vecino con sus datos; la IA solo para lo que las reglas no cubren.

Spec: docs/desarrollo/70-asistente-de-compra.md. Solo lectura: no cambia pedidos, pagos ni saldo.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from decimal import Decimal

from . import cycle as cycles
from . import logistics, reference, wallet
from .domain import MIN_ORDERS_PER_GROUP, BusinessRuleError
from .ia import AIClient
from .store import InMemoryStore

DAILY_AI_LIMIT = 10  # S-353
MAX_QUESTION = 300  # AS-02
MAX_TOKENS = 400  # S-352
RULES = ("Se paga por adelantado con Yape o Plin, con el código del pedido. Se puede pedir hasta el miércoles a las 8 de la "
         "noche. Cada grupo de edificios necesita 8 pedidos verificados para que la compra vaya; si no llega, se devuelve "
         "todo. Se entrega el sábado en la portería. Se paga el precio máximo y lo que baja vuelve como saldo. Los reclamos "
         "se hacen dentro de las 24 horas de la entrega, con foto.")  # S-355
SUGGESTIONS = ["¿Dónde está mi pedido?", "¿Cuándo llega?", "¿Cuánto ahorré?", "¿Cuánto cuesta la papa amarilla?",
               "¿Mi edificio ya llegó al mínimo?"]
# S-351: palabras (sin tildes) de cada tema que se responde con datos; el orden decide si una pregunta toca dos
TOPICS = (
    ("precio", r"precio|cuesta|cuanto (esta|sale|vale)|vale |caro|barat"),
    ("ahorro", r"ahorr|devuelv|devolu|saldo|reembols"),
    ("grupo", r"grupo|minimo|faltan|cuantos (pedidos|vecinos)|llego al|edificio"),
    ("entrega", r"cuando (llega|entregan|me llega|traen)|entrega|horario|ventana|que dia|sabado"),
    ("pedido", r"pedido|estado|donde esta|ya (llego|pagaron|verificaron)|seguimiento|mi compra"),
)
SYSTEM = (
    "Eres el asistente de compra de Yapa, compras grupales semanales de vecinos en Lima. Respondes en español "
    "neutro, en 1 a 3 frases, usando SOLO los datos del vecino que te paso en JSON. Si el dato no está, dilo y "
    "sugiere escribir al equipo desde Mis pedidos. No prometas precios ni fechas que no estén en los datos. Los montos van en soles (S/). "
    'Responde solo un objeto JSON {"respuesta":"..."}.'
)


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def _money(value) -> str:
    return f"S/ {Decimal(value):.2f}"


def _orders(store: InMemoryStore, customer_id: int) -> list:
    # S-356: la semana manda; el número solo desempata dentro de la misma semana
    return sorted((o for o in store.orders.values() if o.customer_id == customer_id), key=lambda o: (o.cycle, o.order_id),
                  reverse=True)


def _current_order(store: InMemoryStore, customer_id: int, now: datetime):
    current = cycles.cycle_id(now)
    mine = _orders(store, customer_id)
    return next((o for o in mine if o.cycle == current and o.status != "CANCELADO_POR_CLIENTE"), None) or \
        (mine[0] if mine else None)


def _last_settled(store: InMemoryStore, customer_id: int):
    for order in _orders(store, customer_id):
        result = store.settlements.get(order.cycle)
        settled = result.orders.get(order.order_id) if result else None
        if settled is not None and order.status == "LIQUIDADO":
            return order, settled
    return None, None


def _prices(store: InMemoryStore, now: datetime) -> list[dict]:
    catalog = store.catalog_for(cycles.cycle_id(now))
    rows = []
    for p in catalog.values():
        if not p.active:
            continue
        lowest = p.price_with_commission(min(t.base_price for t in p.tiers))
        market = reference.current_references(store, p.product_id, cycles.to_lima(now).date()).get("SUPERMERCADO")
        rows.append({"nombre": p.name, "unidad": p.unit, "precio": f"{p.max_unit_price():.2f}",
                     "puede_bajar_a": f"{lowest:.2f}", "supermercado": f"{market.price:.2f}" if market else None})
    return rows


def context(store: InMemoryStore, customer_id: int, now: datetime, progress: dict) -> dict:
    """S-352: solo los datos de este vecino y los precios de la semana."""
    customer = store.customers[customer_id]
    current = cycles.cycle_id(now)
    order = _current_order(store, customer_id, now)
    last, settled = _last_settled(store, customer_id)
    return {
        "vecino": customer.name,
        "reglas_de_yapa": RULES,
        "semana": {"abierta": cycles.is_open(now), "cierre": "miércoles a las 8 de la noche",
                   "entrega": f"sábado {logistics.delivery_day(current)}"},
        "pedido": None if order is None else {
            "numero": order.order_id, "semana_de_entrega": f"sábado {logistics.delivery_day(order.cycle)}",
            "estado": logistics.order_status(store, order)["titulo"], "total": f"{order.total:.2f}",
            "pago": "verificado" if order.payment_status == "VERIFICADO" else "por verificar",
            "productos": ", ".join(f"{store.catalog_for(order.cycle).get(l.product_id, store.products.get(l.product_id)).name}"
                                   f" {l.quantity.normalize():f}" for l in order.lines if l.product_id in store.products)},
        "ultimo_ahorro": None if last is None else {"pedido": last.order_id, "pagaste": f"{settled.paid:.2f}",
                                                    "costo_final": f"{settled.final_amount:.2f}",
                                                    "te_devolvimos": f"{settled.refund_amount:.2f}"},
        "saldo": f"{wallet.balance(store, customer_id):.2f}",
        "grupo": {"verificados": progress["verificados"], "minimo": progress["minimo"]},
        "precios": _prices(store, now),
    }


def _topic(question: str) -> str | None:
    plain = _plain(question)
    return next((name for name, pattern in TOPICS if re.search(pattern, plain)), None)


def _by_data(topic: str, question: str, ctx: dict) -> str:
    """S-351: respuestas armadas con los datos, sin IA."""
    order, week = ctx["pedido"], ctx["semana"]
    if topic == "pedido":
        if order is None:
            return "Todavía no tienes pedidos. " + ("Puedes pedir hasta el " + week["cierre"] + "." if week["abierta"]
                                                    else "La próxima semana abre el lunes.")
        paid = "" if "pago" in _plain(order["estado"]) else f", pago {order['pago']}"
        return (f"Tu pedido {order['numero']}: {order['estado']}. Total {_money(order['total'])}{paid}. "
                f"Se entrega el {order['semana_de_entrega']}.")
    if topic == "entrega":
        when = order["semana_de_entrega"] if order else week["entrega"]
        open_note = f" Puedes pedir o cambiar tu pedido hasta el {week['cierre']}." if week["abierta"] else ""
        return f"Entregamos el {when} en la portería o recepción de tu edificio.{open_note}"
    if topic == "ahorro":
        saved = ctx["ultimo_ahorro"]
        head = (f"En tu pedido {saved['pedido']} pagaste {_money(saved['pagaste'])}, costó {_money(saved['costo_final'])} "
                f"y te devolvimos {_money(saved['te_devolvimos'])}. " if saved else
                "Aún no tienes un pedido liquidado: el ahorro se calcula después de la entrega. ")
        return head + f"Tu saldo es {_money(ctx['saldo'])} y lo puedes usar en tu próximo pedido."
    if topic == "grupo":
        group = ctx["grupo"]
        missing = max(0, group["minimo"] - group["verificados"])
        return (f"Tu grupo lleva {group['verificados']} de {group['minimo']} pedidos verificados esta semana. "
                + ("¡Ya llegó al mínimo: la compra va!" if not missing else f"Faltan {missing} para que la compra vaya."))
    plain = _plain(question)
    found = [p for p in ctx["precios"] if _plain(p["nombre"]) in plain] or \
        [p for p in ctx["precios"] if _plain(p["nombre"]).split()[0] in plain.split()]
    if not found:
        cheapest = sorted(ctx["precios"], key=lambda p: Decimal(p["precio"]))[:4]
        return "Algunos precios de esta semana: " + "; ".join(f"{p['nombre']} {_money(p['precio'])} por {p['unidad']}"
                                                               for p in cheapest) + ". Pregunta por un producto para más detalle."
    parts = []
    for p in found[:3]:
        line = f"{p['nombre']}: {_money(p['precio'])} por {p['unidad']} como máximo; puede bajar hasta {_money(p['puede_bajar_a'])} si el grupo compra más"
        if p["supermercado"]:
            line += f" (en el súper, {_money(p['supermercado'])})"
        parts.append(line)
    return ". ".join(parts) + "."


def _use_ai(store: InMemoryStore, customer_id: int, now: datetime) -> bool:
    """S-353: cuenta solo las preguntas que van a la IA."""
    key = f"asistente:{customer_id}:{cycles.to_lima(now).date().isoformat()}"
    if store.ia_usage.get(key, 0) >= DAILY_AI_LIMIT:
        return False
    store.ia_usage[key] = store.ia_usage.get(key, 0) + 1
    return True


def answer(store: InMemoryStore, ai: AIClient | None, customer_id: int, question, now: datetime, progress: dict) -> dict:
    """AS-01..AS-05."""
    question = str(question or "").strip()[:MAX_QUESTION]
    if not question:
        raise BusinessRuleError("QUESTION_REQUIRED", "Escribe tu pregunta.")
    ctx = context(store, customer_id, now, progress)
    topic = _topic(question)
    if topic is not None:
        return {"respuesta": _by_data(topic, question, ctx), "tema": topic, "fuente": "datos", "sugerencias": []}
    if ai is not None and _use_ai(store, customer_id, now):
        try:
            reply, _ = ai.ask_json(SYSTEM, json.dumps({"datos": ctx, "pregunta": question}, ensure_ascii=False),
                                   max_tokens=MAX_TOKENS)
            text = str(reply.get("respuesta") or "").strip()[:800]
            if text:
                return {"respuesta": text, "tema": "otro", "fuente": "ia", "sugerencias": []}
        except BusinessRuleError:
            pass
    return {"respuesta": "Esa no la sé responder todavía. Puedo contarte cómo va tu pedido, cuándo llega, cuánto ahorraste, "
                         "los precios de la semana o cuánto le falta a tu grupo.",
            "tema": "otro", "fuente": "sin_respuesta", "sugerencias": SUGGESTIONS}
