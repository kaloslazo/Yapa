"""Alta de vecinos y reinicio del PIN (iteración 24).

Spec: docs/desarrollo/24-alta-vecinos.md (S-133..S-138).
"""

from __future__ import annotations

import re
import unicodedata
import secrets
from datetime import datetime

from .auth import _check_pin, set_pin
from .domain import BusinessRuleError, Customer
from .store import InMemoryStore


def _check_admin(store: InMemoryStore, by: str) -> None:
    if by not in store.admins:  # AV-01
        raise BusinessRuleError("NOT_AUTHORIZED", "Solo el administrador de Yapa da de alta vecinos.")


def new_pin() -> str:
    """S-136: 6 dígitos al azar que cumplen S-66."""
    while True:
        pin = f"{secrets.randbelow(1_000_000):06d}"
        try:
            _check_pin(pin)
            return pin
        except BusinessRuleError:
            continue


def referral_code(customer: Customer) -> str:
    """S-161: primer nombre en mayúsculas, sin tildes, y el número de cliente (Ana Torres, 101 -> ANA101)."""
    first = (customer.name.split() or [""])[0]
    plain = "".join(ch for ch in unicodedata.normalize("NFKD", first) if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z]", "", plain.upper()) + str(customer.customer_id)


def find_by_referral(store: InMemoryStore, code: str) -> Customer:
    """AZ-05, S-162."""
    wanted = (code or "").strip().upper()
    for customer in store.customers.values():
        if referral_code(customer) == wanted:
            return customer
    raise BusinessRuleError("REFERRAL_NOT_FOUND", "Ese código de referido no existe.")


def register_customer(store: InMemoryStore, name: str, phone: str, zone_id: str, consent: bool, *, by: str,
                      now: datetime, referral: str = "") -> tuple[Customer, str]:
    """AV-02..AV-06. Devuelve el cliente y su PIN inicial, que no se guarda."""
    _check_admin(store, by)
    name = (name or "").strip()
    if not name:  # AV-02
        raise BusinessRuleError("NAME_REQUIRED", "Escribe el nombre del vecino.")
    phone = (phone or "").strip()
    if not re.fullmatch(r"9\d{8}", phone):  # AV-03, S-134
        raise BusinessRuleError("INVALID_PHONE", "El celular debe tener 9 dígitos y empezar con 9.")
    if any(c.phone == phone for c in store.customers.values()):
        raise BusinessRuleError("PHONE_ALREADY_REGISTERED", "Ese celular ya está registrado.")
    if zone_id not in store.zones:  # AV-04, S-138
        raise BusinessRuleError("ZONE_NOT_FOUND", "La zona no existe.")
    if not consent:  # AV-05, S-133 (Ley 29733)
        raise BusinessRuleError("CONSENT_REQUIRED", "Sin el consentimiento del vecino no se guardan sus datos.")
    referred_by = find_by_referral(store, referral).customer_id if (referral or "").strip() else None  # AZ-05
    customer_id = max(store.customers, default=0) + 1  # S-135
    customer = Customer(customer_id, name, zone_id, phone=phone, consent_at=now, referred_by=referred_by)
    store.add_customer(customer)
    pin = new_pin()
    set_pin(store, customer_id, pin)
    return customer, pin


def reset_pin(store: InMemoryStore, customer_id: int, *, by: str) -> str:
    """AV-07, S-137: PIN nuevo; una credencial nueva también quita el bloqueo."""
    _check_admin(store, by)
    if customer_id not in store.customers:
        raise BusinessRuleError("CUSTOMER_NOT_FOUND", "El cliente no está registrado.")
    pin = new_pin()
    set_pin(store, customer_id, pin)
    return pin
