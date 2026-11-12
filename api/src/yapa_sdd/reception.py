"""Recepción en el edificio (iteración 55).

Spec: docs/desarrollo/55-personal-por-rol.md. Confirma quien recibe en la zona: su portería o su admin de zona (S-294).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from . import partners
from .domain import BusinessRuleError
from .fulfillment import is_attended
from .store import InMemoryStore


@dataclass(frozen=True)
class Reception:
    cycle: str
    zone_id: str
    order_ids: tuple[int, ...]
    received_by: str
    received_at: datetime


def _check_receiver(store: InMemoryStore, zone_id: str, by) -> None:
    """PO-02: la portería de esa zona o su admin de zona; nadie más."""
    concierge = partners.active(store, by, partners.CONCIERGE)
    if concierge is not None:
        if concierge.zone_id != zone_id:
            raise BusinessRuleError("FOREIGN_ZONE", "Esta entrega es de otra zona.")
        return
    if isinstance(by, int) and by in store.customers:
        zone = store.zones.get(zone_id)
        if zone is None or zone.admin_id != by:
            raise BusinessRuleError("FOREIGN_ZONE", "Solo el admin de la zona confirma su recepción.")
        return
    raise BusinessRuleError("NOT_AUTHORIZED", "Confirma la recepción la portería o el admin de la zona.")


def for_zone(store: InMemoryStore, cycle: str, zone_id: str) -> dict:
    """PO-01, S-293: por pedido solo el número, el vecino y sus bolsas; sin productos, montos ni celulares."""
    delivery = store.deliveries.get((cycle, zone_id))
    failure = store.failed_deliveries.get((cycle, zone_id))
    received = store.receptions.get((cycle, zone_id))
    if delivery is not None:
        order_ids = delivery.order_ids
    elif failure is not None:
        order_ids = failure.order_ids
    else:
        order_ids = tuple(o.order_id for o in store.orders_in_cycle(cycle) if o.zone_id == zone_id and is_attended(store, o))
    state = ("recibida" if received else "entregada" if delivery else "fallida" if failure else "pendiente")
    zone = store.zones[zone_id]
    # Iteración 63: hitos derivados de hechos existentes, sin nuevos estados de negocio.
    bags = [store.bags.get(order_id, []) for order_id in order_ids]
    ready = bool(bags) and all(bags)
    dispatch = store.dispatches.get((cycle, zone_id))
    milestones = []
    if ready:
        milestones.append({"estado": "listo", "hora": max(min(b.packed_at for b in group) for group in bags).isoformat()})
    if dispatch or delivery:
        milestones.append({"estado": "en_camino", "hora": (dispatch.at if dispatch else delivery.delivered_at).isoformat()})
    if delivery:
        milestones.append({"estado": "entregada", "hora": delivery.delivered_at.isoformat()})
    if failure:
        milestones.append({"estado": "fallida", "hora": failure.registered_at.isoformat()})
    if received:
        milestones.append({"estado": "recibida", "hora": received.received_at.isoformat()})
    progress = ("recibida" if received else "entregada" if delivery else "fallida" if failure
                else "en_camino" if dispatch else "listo" if ready else "preparando" if order_ids else "sin_pedidos")
    return {
        "ciclo": cycle,
        "zona": {"id": zone.zone_id, "nombre": zone.name, "distrito": zone.district},
        "estado": state,
        "seguimiento": progress,
        "hitos": sorted(milestones, key=lambda item: datetime.fromisoformat(item["hora"])),
        "entrego": ({"recibe": delivery.received_by, "hora": delivery.delivered_at.isoformat()} if delivery else None),
        "confirmo": ({"por": received.received_by, "hora": received.received_at.isoformat()} if received else None),
        "pedidos": [{"id": order_id, "vecino": store.customers[store.orders[order_id].customer_id].name,
                     "bolsas": len(store.bags.get(order_id, []))} for order_id in sorted(order_ids)],
    }


def confirm_reception(store: InMemoryStore, cycle: str, zone_id: str, *, by, now: datetime) -> Reception:
    """PO-02..PO-04, S-294: una sola vez y solo sobre una entrega registrada; no mueve dinero."""
    _check_receiver(store, zone_id, by)
    delivery = store.deliveries.get((cycle, zone_id))
    if delivery is None:  # PO-03
        raise BusinessRuleError("DELIVERY_NOT_FOUND", "El transportista todavía no registra la entrega de esta zona.")
    if (cycle, zone_id) in store.receptions:  # PO-04
        raise BusinessRuleError("ALREADY_CONFIRMED", "Esta entrega ya fue confirmada.")
    received = Reception(cycle, zone_id, delivery.order_ids, str(by), now)
    store.receptions[(cycle, zone_id)] = received
    return received
