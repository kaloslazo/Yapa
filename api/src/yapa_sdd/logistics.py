"""Logística propia de Yapa: flete de compra, salida a reparto y seguimiento del pedido (iteración 58).

Spec: docs/desarrollo/58-logistica-propia.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from . import cycle as cycles
from . import notices, partners
from .domain import BusinessRuleError, Order
from .fulfillment import _check_purchase, _ready_orders, check_courier, check_role, is_attended
from .metrics import OperatingCosts
from .store import InMemoryStore


ESTIMATED_FREIGHT = Decimal("180")  # S-307: cotización más baja encontrada el 09/11/2026 (S/ 180–320)
MAX_FREIGHT = Decimal("2000")  # S-306
PACKING, SUPPORT = Decimal("1.60"), Decimal("0.73")  # S-307: los mismos de S-96 y S-97
STEPS = ("Pedido", "Pago verificado", "Comprado", "Armado", "En camino", "Entregado", "Te devolvemos")  # S-309


@dataclass(frozen=True)
class Freight:
    cycle: str
    company: str
    amount: Decimal
    by: str
    at: datetime


@dataclass(frozen=True)
class Dispatch:
    cycle: str
    zone_id: str
    order_ids: tuple[int, ...]
    by: str
    at: datetime


def register_freight(store: InMemoryStore, cycle: str, company, amount, *, by, now: datetime) -> Freight:
    check_role(store, by, partners.BUYER)  # FL-01
    cycles.check_cycle_id(cycle)
    if cycles.to_lima(now) < cycles.closes_at(cycle):  # FL-02
        raise BusinessRuleError("CYCLE_STILL_OPEN", "El ciclo sigue abierto; el flete se registra después del cierre.")
    if cycle in store.freights:  # FL-03
        raise BusinessRuleError("FREIGHT_ALREADY_REGISTERED", "El flete de esta semana ya está registrado.")
    name = str(company or "").strip()
    if not name or len(name) > 80:  # FL-04
        raise BusinessRuleError("INVALID_FREIGHT", "Escribe el nombre de la empresa del flete (hasta 80 caracteres).")
    try:
        value = Decimal(str(amount).strip())
    except (InvalidOperation, ValueError):
        value = None
    if value is None or not value.is_finite() or value <= 0 or value > MAX_FREIGHT or value.as_tuple().exponent < -2:
        raise BusinessRuleError("INVALID_AMOUNT", f"El monto del flete va de S/ 0.01 a S/ {MAX_FREIGHT}, con céntimos.")
    freight = Freight(cycle, name, value.quantize(Decimal("0.01")), by, now)
    store.freights[cycle] = freight
    return freight


def real_costs(store: InMemoryStore, cycle: str) -> tuple[OperatingCosts, Decimal, bool]:
    """MR-01, S-307: el flete de la semana repartido entre los pedidos atendidos; sin registrar, S/ 180 estimados."""
    registered = store.freights.get(cycle)
    freight = registered.amount if registered else ESTIMATED_FREIGHT
    attended = sum(1 for o in store.orders_in_cycle(cycle) if is_attended(store, o))
    trip = (freight / attended).quantize(Decimal("0.01")) if attended else Decimal("0")
    return OperatingCosts("REAL", trip, PACKING, SUPPORT, Decimal("0")), freight, registered is None


def dispatch_zone(store: InMemoryStore, cycle: str, zone_id: str, *, by, now: datetime) -> Dispatch:
    """SR-01, SR-02, S-308: el reparto sale hacia la zona y cada vecino recibe el aviso."""
    check_courier(store, by)
    if zone_id not in store.zones:
        raise BusinessRuleError("ZONE_NOT_FOUND", "La zona no existe.")
    if (cycle, zone_id) in store.deliveries or (cycle, zone_id) in store.failed_deliveries:
        raise BusinessRuleError("ZONE_ALREADY_CLOSED", "Esta zona ya se entregó o ya falló en el ciclo.")
    if (cycle, zone_id) in store.dispatches:
        raise BusinessRuleError("ZONE_ALREADY_DISPATCHED", "El reparto ya salió hacia esta zona.")
    orders = _ready_orders(store, cycle, zone_id)
    _check_purchase(store, cycle)
    dispatch = Dispatch(cycle, zone_id, tuple(o.order_id for o in orders), by, now)
    store.dispatches[(cycle, zone_id)] = dispatch
    zone = store.zones[zone_id].name
    for order in orders:
        notices.add(store, order.customer_id, "EN_CAMINO", "Tu pedido va en camino",
                    f"Tu pedido {order.order_id} de la semana {cycle} ya salió hacia {zone}.", now)
    return dispatch


METHOD_NAMES = {"YAPE": "Yape", "PLIN": "Plin", "SALDO": "Saldo"}


def _iso(moment: datetime | None) -> str | None:
    return cycles.to_lima(moment).isoformat() if moment else None


def _hour(moment: datetime) -> str:
    return cycles.to_lima(moment).strftime("%H:%M")


def _qty(value: Decimal) -> str:
    return format(value.normalize(), "f")


def delivery_day(cycle: str) -> str:
    """S-311: la entrega es el sábado del ciclo (lunes de apertura + 5 días)."""
    return (cycles.opens_at(cycle) + timedelta(days=5)).strftime("%d/%m")


def _verified_at(store: InMemoryStore, order: Order) -> datetime | None:
    """S-310: la hora del registro de caja; si pagó todo con saldo, la del registro del pedido."""
    entries = [e.at for e in store.cash_in if e.order_id == order.order_id and e.at]
    return min(entries) if entries else (order.registered_at if order.payment_status == "VERIFICADO" else None)


def _shortage_notes(store: InMemoryStore, order: Order, sources: tuple[str, ...]) -> list[str]:
    catalog = store.catalog_for(order.cycle)
    notes = []
    for s in store.shortages:
        if s.order_id != order.order_id or s.source not in sources:
            continue
        product = catalog.get(s.product_id)
        name, unit = (product.name, product.unit) if product else (s.product_id, "")
        what = "Faltó" if s.source == "COMPRA" else "Llegó dañado"
        if s.quantity > s.from_buffer:
            notes.append(f"{what} {_qty(s.quantity - s.from_buffer)} {unit} de {name}: vuelve como saldo")
        if s.from_buffer > 0:
            notes.append(f"{_qty(s.from_buffer)} {unit} de {name} repuesto del colchón")
    return notes


def _delivery(store: InMemoryStore, order: Order):
    delivery = store.deliveries.get((order.cycle, order.zone_id))
    return delivery if delivery and order.order_id in delivery.order_ids else None


def tracking(store: InMemoryStore, order: Order) -> list[dict]:
    """SG-01, SG-03, S-309, S-312: los siete pasos, cuáles pasaron, a qué hora y con qué detalle."""
    key = (order.cycle, order.zone_id)
    delivery = _delivery(store, order)
    dispatch = store.dispatches.get(key)
    bags = store.bags.get(order.order_id, [])
    bought = store.purchases.get(order.cycle)
    zone = store.zones[order.zone_id].name
    settled = store.settlements.get(order.cycle)
    settled = settled.orders.get(order.order_id) if settled else None
    verified = order.payment_status == "VERIFICADO"
    method = METHOD_NAMES.get(order.payment_method, order.payment_method)

    received = store.receptions.get(key)
    delivered_detail = ""
    if delivery:
        delivered_detail = f"Lo recibió {delivery.received_by}"
        if received:
            delivered_detail += f". La portería lo confirmó a las {_hour(received.received_at)}"
    packed = ""
    if bags:
        packed = f"{len(bags)} {'bolsa' if len(bags) == 1 else 'bolsas'}, con foto"
        damaged = _shortage_notes(store, order, ("DANADO",))
        packed = ". ".join([packed] + damaged)
    returned = settled.refund_amount if settled and order.status == "LIQUIDADO" else Decimal("0")

    pasos = (
        (True, order.registered_at,
         f"{len(order.lines)} {'producto' if len(order.lines) == 1 else 'productos'} · S/ {order.total:.2f}"),
        (verified, _verified_at(store, order) if verified else None, f"{method} · S/ {order.total:.2f}" if verified else ""),
        (bought is not None, bought.at if bought else None,
         ". ".join(_shortage_notes(store, order, ("COMPRA",))) or "Llegó todo" if bought else ""),
        (bool(bags), max(b.packed_at for b in bags) if bags else None, packed),
        (dispatch is not None or delivery is not None,
         dispatch.at if dispatch else (delivery.delivered_at if delivery else None),
         f"Salió hacia {zone}" if dispatch or delivery else ""),  # S-308
        (delivery is not None, delivery.delivered_at if delivery else None, delivered_detail),
        (order.status == "LIQUIDADO", None, f"S/ {returned:.2f} a tu saldo" if order.status == "LIQUIDADO" else ""),
    )
    return [{"paso": step, "hecho": done, "cuando": _iso(when) if done else None, "detalle": detail}
            for step, (done, when, detail) in zip(STEPS, pasos)]


def order_status(store: InMemoryStore, order: Order) -> dict:
    """SG-02, S-311: el estado del pedido en una frase."""
    def status(titulo: str, detalle: str = "") -> dict:
        return {"titulo": titulo, "detalle": detalle}

    finals = {
        "CANCELADO_POR_CLIENTE": status("Cancelaste este pedido"),
        "CANCELADO": status("Anulado: el pago no llegó antes del cierre", "Si usaste saldo, volvió a tu saldo."),
        "NO_ATENDIDO": status("Tu grupo no llegó a 8 pedidos", "Te devolvemos todo a tu medio de pago."),
        "NO_ENTREGADO": status("No se pudo entregar", "Te devolvimos todo menos el envío, como saldo."),
    }
    if order.status in finals:
        return finals[order.status]
    zone = store.zones[order.zone_id].name
    day = delivery_day(order.cycle)
    if order.status == "LIQUIDADO":
        settled = store.settlements[order.cycle].orders[order.order_id]
        return status(f"Te devolvimos S/ {settled.refund_amount:.2f}", "Ya está en tu saldo para tu próxima compra.")
    delivery = _delivery(store, order)
    if delivery:
        return status(f"Entregado en {zone}", f"Lo recibió {delivery.received_by} a las {_hour(delivery.delivered_at)}.")
    dispatch = store.dispatches.get((order.cycle, order.zone_id))
    if dispatch:
        return status(f"En camino a {zone}", f"Salió a las {_hour(dispatch.at)}.")
    if store.bags.get(order.order_id):
        return status("Armado", f"Sale el sábado {day} hacia {zone}.")
    if order.cycle in store.purchases:
        return status("Comprado", f"Armamos tu bolsa para el sábado {day}.")
    if order.payment_status == "VERIFICADO":
        return status("Pago verificado", f"Compramos el jueves y entregamos el sábado {day}.")
    return status("Falta tu pago", f"Paga S/ {order.paid_external:.2f} con el código {order.operation_code} "
                                   "antes del miércoles a las 20:00.")


def order_photos(store: InMemoryStore, order: Order) -> dict:
    """SG-05, S-313: las fotos que el sistema guardó para este pedido."""
    delivery = _delivery(store, order)
    return {"entrega": delivery.photo if delivery else None,
            "bolsas": [bag.photo for bag in store.bags.get(order.order_id, [])]}
