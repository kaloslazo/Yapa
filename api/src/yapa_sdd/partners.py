"""Cuentas de proveedores y transportistas (iteración 54) y del personal por rol (iteración 55).

Specs: docs/desarrollo/54-proveedores-y-transportistas.md y 55-personal-por-rol.md. Las crea el administrador
(S-278, S-289).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime

from . import auth
from .domain import BusinessRuleError, Supplier
from .store import InMemoryStore


DRIVER = "transportista"
SUPPLIER = "proveedor"
BUYER = "compras"  # S-291
PACKER = "armador"  # S-290
SUPPORT = "atencion"  # S-292
CONCIERGE = "porteria"  # S-293
STAFF_KINDS = (BUYER, PACKER, SUPPORT, CONCIERGE)
STAFF_NAMES = {BUYER: "encargado de compras", PACKER: "armador", SUPPORT: "atención al cliente", CONCIERGE: "portería"}
USER = re.compile(r"[a-z0-9-]{3,30}")  # S-279


@dataclass(frozen=True)
class Partner:
    user: str
    kind: str
    name: str
    created_by: str
    created_at: datetime
    supplier_id: str | None = None
    active: bool = True
    zone_id: str | None = None  # S-293: la zona de la portería


def _check_admin(store: InMemoryStore, by: str) -> None:
    if by not in store.admins:  # CX-01
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo el administrador de Yapa maneja estas cuentas.")


def _check_user(store: InMemoryStore, user: str) -> str:
    user = (user or "").strip()
    if not USER.fullmatch(user):  # CX-02
        raise BusinessRuleError("INVALID_USER", "El usuario lleva de 3 a 30 minúsculas, números o guiones.")
    if user in store.admins or user in store.partners:
        raise BusinessRuleError("USER_TAKEN", "Ese usuario ya existe.")
    return user


def _check_password(password: str) -> None:
    if len(password or "") < auth.MIN_ADMIN_PASSWORD:  # CX-03
        raise BusinessRuleError("INVALID_PASSWORD", f"La contraseña debe tener al menos {auth.MIN_ADMIN_PASSWORD} caracteres.")


def _save(store: InMemoryStore, partner: Partner, password: str) -> Partner:
    store.partners[partner.user] = partner
    store.credentials[(partner.kind, partner.user)] = auth._new_credential(password)
    return partner


def create_driver(store: InMemoryStore, user: str, name: str, password: str, *, by: str, now: datetime) -> Partner:
    _check_admin(store, by)
    user = _check_user(store, user)
    name = (name or "").strip()
    if not name:
        raise BusinessRuleError("NAME_REQUIRED", "Escribe el nombre del transportista.")
    _check_password(password)
    return _save(store, Partner(user, DRIVER, name, by, now), password)


def create_supplier_account(store: InMemoryStore, user: str, supplier_id: str, password: str, *, by: str,
                            now: datetime, name: str = "") -> Partner:
    """CX-04, S-283: un proveedor aliado por cuenta; con código nuevo y nombre se registra."""
    _check_admin(store, by)
    user = _check_user(store, user)
    supplier_id, name = (supplier_id or "").strip(), (name or "").strip()
    supplier = store.suppliers.get(supplier_id)
    if supplier is None and not (supplier_id and name):
        raise BusinessRuleError("SUPPLIER_NOT_FOUND", "Ese proveedor no está registrado; escribe su nombre para darlo de alta.")
    if supplier is not None and not supplier.allied:
        raise BusinessRuleError("SUPPLIER_NOT_ALLIED", "Ese proveedor no es aliado de Yapa.")
    _check_password(password)
    if supplier is None:
        supplier = Supplier(supplier_id, name)
        store.add_supplier(supplier)
    return _save(store, Partner(user, SUPPLIER, supplier.name, by, now, supplier_id=supplier_id), password)


def create_staff(store: InMemoryStore, user: str, kind: str, name: str, password: str, *, by: str, now: datetime,
                 zone_id: str | None = None) -> Partner:
    """CX-07, CX-08, S-289: compras, armado, atención o portería; la portería apunta a su zona."""
    _check_admin(store, by)
    if kind not in STAFF_KINDS:
        raise BusinessRuleError("INVALID_INPUT", "Elige compras, armado, atención o portería.")
    user = _check_user(store, user)
    name = (name or "").strip()
    if not name:
        raise BusinessRuleError("NAME_REQUIRED", f"Escribe el nombre de la persona de {STAFF_NAMES[kind]}.")
    if kind != CONCIERGE:
        zone_id = None
    elif (zone_id or "").strip() not in store.zones:
        raise BusinessRuleError("ZONE_NOT_FOUND", "Elige la zona de esta portería.")
    else:
        zone_id = zone_id.strip()
    _check_password(password)
    return _save(store, Partner(user, kind, name, by, now, zone_id=zone_id), password)


def _find(store: InMemoryStore, user: str) -> Partner:
    partner = store.partners.get(user)
    if partner is None:
        raise BusinessRuleError("ACCOUNT_NOT_FOUND", "Esa cuenta no existe.")
    return partner


def deactivate(store: InMemoryStore, user: str, *, by: str) -> Partner:
    """CX-05, S-280: sin credencial no entra, y su sesión se cierra (SG-05)."""
    _check_admin(store, by)
    partner = _find(store, user)
    store.credentials.pop((partner.kind, partner.user), None)
    store.partners[user] = replace(partner, active=False)
    return store.partners[user]


def set_password(store: InMemoryStore, user: str, password: str, *, by: str) -> Partner:
    """S-280: una contraseña nueva reactiva la cuenta."""
    _check_admin(store, by)
    partner = _find(store, user)
    _check_password(password)
    return _save(store, replace(partner, active=True), password)


def active(store: InMemoryStore, user: str, kind: str) -> Partner | None:
    partner = store.partners.get(user)
    return partner if partner is not None and partner.kind == kind and partner.active else None


def can(store: InMemoryStore, by, *kinds: str) -> bool:
    """El administrador, o una cuenta activa de alguno de esos tipos (AM-02, CP-04, AT-04)."""
    return by in store.admins or any(active(store, by, kind) is not None for kind in kinds)
