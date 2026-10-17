"""Zonas de vecinos: crear, activar, unirse, unir grupos y transferir admin (iteración 5).

Spec: docs/desarrollo/05-zonas-vecinos.md. Ninguna función mueve dinero (ZN-08).
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import datetime
from decimal import Decimal

from . import cycle
from .domain import PILOT_DISTRICTS, BusinessRuleError, Customer, Zone
from .store import InMemoryStore


MEMBER_RADIUS_M = 300  # S-25
MERGE_DISTANCE_M = 500  # S-26
NEW_ZONE_STOP_COST = Decimal("40")  # S-32
RECEPTION_KINDS = frozenset({"PORTERIA", "ENCARGADO", "ADMIN"})  # S-28


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """S-27: distancia en línea recta (Haversine), en metros."""
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _customer(store: InMemoryStore, customer_id: int) -> Customer:
    customer = store.customers.get(customer_id)
    if customer is None:
        raise BusinessRuleError("CUSTOMER_NOT_FOUND", "El cliente no está registrado.")
    return customer


def _zone(store: InMemoryStore, zone_id: str) -> Zone:
    zone = store.zones.get(zone_id)
    if zone is None:
        raise BusinessRuleError("ZONE_NOT_FOUND", "La zona no existe.")
    return zone


def _admin_zone(store: InMemoryStore, zone_id: str, admin_id: int) -> Zone:
    zone = _zone(store, zone_id)
    if zone.admin_id != admin_id:
        raise BusinessRuleError("NOT_ZONE_ADMIN", "Solo el admin de la zona puede hacer esto.")
    return zone


def _is_admin_somewhere(store: InMemoryStore, customer_id: int) -> bool:
    return any(zone.admin_id == customer_id for zone in store.zones.values())


def _check_can_move(store: InMemoryStore, customer_id: int) -> None:
    """S-30: con un pedido sin liquidar no se cambia de zona."""
    if any(o.customer_id == customer_id and o.status == "REGISTRADO" for o in store.orders.values()):
        raise BusinessRuleError("HAS_ACTIVE_ORDER", "Tienes un pedido en curso; cámbiate de zona después de recibirlo.")


def _check_coordinates(lat, lon) -> None:
    """HR-01, HR-02: coordenadas numéricas, finitas y en rango."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        raise BusinessRuleError("INVALID_LOCATION", "La ubicación no es válida.")
    if not (math.isfinite(lat) and math.isfinite(lon)) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise BusinessRuleError("INVALID_LOCATION", "La ubicación no es válida.")


def set_location(store: InMemoryStore, customer_id: int, lat, lon) -> Customer:
    """HR-01, S-109: el vecino registra dónde vive."""
    customer = _customer(store, customer_id)
    _check_coordinates(lat, lon)
    located = replace(customer, lat=float(lat), lon=float(lon))
    store.add_customer(located)
    return located


def _check_open(now: datetime) -> None:
    if not cycle.is_open(now):  # S-31
        raise BusinessRuleError("CYCLE_CLOSED", "Las zonas solo se unen o separan con el ciclo abierto.")


def create_zone(store: InMemoryStore, admin_id: int, *, name: str, district: str, lat: float, lon: float,
                now: datetime) -> Zone:
    """ZN-01."""
    admin = _customer(store, admin_id)
    if _is_admin_somewhere(store, admin_id):
        raise BusinessRuleError("ALREADY_ADMIN", "Ya eres admin de una zona.")
    if admin.lat is None or admin.lon is None or lat is None or lon is None:
        raise BusinessRuleError("LOCATION_REQUIRED", "Falta la ubicación.")
    _check_coordinates(lat, lon)  # HR-02
    if district not in PILOT_DISTRICTS:
        raise BusinessRuleError("DISTRICT_NOT_IN_PILOT", "Por ahora solo Lince, Jesús María y La Victoria.")
    _check_can_move(store, admin_id)
    zone_id = store.next_zone_id()
    zone = Zone(zone_id, name, district, f"G-{zone_id}", NEW_ZONE_STOP_COST, reception_accepted=False,
                lat=lat, lon=lon, admin_id=admin_id)
    store.add_zone(zone)
    store.add_customer(replace(admin, zone_id=zone_id))
    return zone


def activate_zone(store: InMemoryStore, zone_id: str, admin_id: int, *, reception_kind: str, contact: str) -> Zone:
    """ZN-02: la zona recibe pedidos solo cuando alguien acepta recibirlos."""
    zone = _admin_zone(store, zone_id, admin_id)
    if reception_kind not in RECEPTION_KINDS or not (contact or "").strip():
        raise BusinessRuleError("INVALID_RECEPTION", "Indica portería, encargado o admin, y el nombre de quien recibe.")
    zone.reception_kind = reception_kind
    zone.reception_contact = contact.strip()
    zone.reception_accepted = True
    return zone


def join_zone(store: InMemoryStore, customer_id: int, zone_id: str, *, now: datetime) -> Customer:
    """ZN-03."""
    customer = _customer(store, customer_id)
    zone = _zone(store, zone_id)
    if any(z.admin_id == customer_id and z.zone_id != zone_id for z in store.zones.values()):  # HR-03, S-110
        raise BusinessRuleError("ADMIN_MUST_TRANSFER", "Eres admin de tu zona: primero transfiere el rol.")
    if customer.lat is None or customer.lon is None:
        raise BusinessRuleError("LOCATION_REQUIRED", "Registra tu ubicación para unirte a una zona.")
    _check_zone_location(zone)
    if distance_m(customer.lat, customer.lon, zone.lat, zone.lon) > MEMBER_RADIUS_M:
        raise BusinessRuleError("OUTSIDE_ZONE_RADIUS", "Vives lejos del punto de recepción de esta zona.")
    _check_can_move(store, customer_id)
    moved = replace(customer, zone_id=zone_id)
    store.add_customer(moved)
    return moved


def _check_zone_location(zone: Zone) -> None:
    """S-75: las zonas cargadas antes de la iteración 5 no tienen ubicación."""
    if zone.lat is None or zone.lon is None:
        raise BusinessRuleError("LOCATION_REQUIRED", f"La zona {zone.zone_id} no tiene ubicación registrada.")


def _check_merge(store: InMemoryStore, zone: Zone, target: Zone) -> None:
    if zone.group_id == target.group_id:
        raise BusinessRuleError("SAME_GROUP", "Las zonas ya están unidas.")
    group = [z for z in store.zones.values() if z.group_id == target.group_id]
    for z in [zone] + group:
        _check_zone_location(z)
    if any(distance_m(zone.lat, zone.lon, z.lat, z.lon) > MERGE_DISTANCE_M for z in group):
        raise BusinessRuleError("ZONES_TOO_FAR", "Las zonas están muy lejos para compartir camión.")


def request_merge(store: InMemoryStore, zone_id: str, target_zone_id: str, admin_id: int, *, now: datetime) -> int:
    """ZN-04: el admin de A pide unirse al grupo de B."""
    zone = _admin_zone(store, zone_id, admin_id)
    target = _zone(store, target_zone_id)
    _check_open(now)
    if (zone_id, target_zone_id) in store.merge_requests.values():  # HR-04, S-111
        raise BusinessRuleError("MERGE_ALREADY_REQUESTED", "Ya hay una solicitud igual pendiente.")
    _check_merge(store, zone, target)
    merge_id = store.next_merge_id()
    store.merge_requests[merge_id] = (zone_id, target_zone_id)
    return merge_id


def accept_merge(store: InMemoryStore, merge_id: int, admin_id: int, *, now: datetime) -> Zone:
    """ZN-05: el admin de B acepta; se vuelve a validar por si algo cambió."""
    request = store.merge_requests.get(merge_id)
    if request is None:
        raise BusinessRuleError("MERGE_REQUEST_NOT_FOUND", "La solicitud no existe.")
    zone_id, target_zone_id = request
    target = _admin_zone(store, target_zone_id, admin_id)
    _check_open(now)
    zone = _zone(store, zone_id)
    _check_merge(store, zone, target)
    zone.group_id = target.group_id
    del store.merge_requests[merge_id]
    return zone


def _merge_request(store: InMemoryStore, merge_id: int) -> tuple[str, str]:
    request = store.merge_requests.get(merge_id)
    if request is None:
        raise BusinessRuleError("MERGE_REQUEST_NOT_FOUND", "La solicitud no existe.")
    return request


def reject_merge(store: InMemoryStore, merge_id: int, admin_id: int) -> None:
    """HR-04: el admin de la zona destino dice que no."""
    _, target_zone_id = _merge_request(store, merge_id)
    _admin_zone(store, target_zone_id, admin_id)
    del store.merge_requests[merge_id]


def withdraw_merge(store: InMemoryStore, merge_id: int, admin_id: int) -> None:
    """HR-04: el admin que la pidió la retira."""
    zone_id, _ = _merge_request(store, merge_id)
    _admin_zone(store, zone_id, admin_id)
    del store.merge_requests[merge_id]


def leave_group(store: InMemoryStore, zone_id: str, admin_id: int, *, now: datetime) -> Zone:
    """ZN-06."""
    zone = _admin_zone(store, zone_id, admin_id)
    _check_open(now)
    zone.group_id = f"G-{zone.zone_id}"
    return zone


def transfer_admin(store: InMemoryStore, zone_id: str, admin_id: int, new_admin_id: int) -> Zone:
    """ZN-07: la zona no depende de una sola persona."""
    zone = _admin_zone(store, zone_id, admin_id)
    new_admin = _customer(store, new_admin_id)
    if new_admin.zone_id != zone_id:
        raise BusinessRuleError("NOT_ZONE_MEMBER", "El nuevo admin debe ser vecino de la zona.")
    if _is_admin_somewhere(store, new_admin_id):
        raise BusinessRuleError("ALREADY_ADMIN", "Esa persona ya es admin de una zona.")
    zone.admin_id = new_admin_id
    return zone
