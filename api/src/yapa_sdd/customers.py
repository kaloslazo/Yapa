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


def check_phone(store: InMemoryStore, phone) -> str:
    """AV-03, S-134: 9 dígitos que empiezan con 9, sin repetir."""
    phone = (phone or "").strip()
    if not re.fullmatch(r"9\d{8}", phone):
        raise BusinessRuleError("INVALID_PHONE", "El celular debe tener 9 dígitos y empezar con 9.")
    if any(c.phone == phone for c in store.customers.values()):
        raise BusinessRuleError("PHONE_ALREADY_REGISTERED", "Ese celular ya está registrado.")
    return phone


def register_customer(store: InMemoryStore, name: str, phone: str, zone_id: str, consent: bool, *, by: str,
                      now: datetime, email: str = "", referral: str = "") -> tuple[Customer, str]:
    """AV-02..AV-06. Devuelve el cliente y su PIN inicial, que no se guarda."""
    _check_admin(store, by)
    name = (name or "").strip()
    if not name:  # AV-02
        raise BusinessRuleError("NAME_REQUIRED", "Escribe el nombre del vecino.")
    phone = check_phone(store, phone)  # AV-03, S-134
    email = normalize_email(email, store)
    if zone_id not in store.zones:  # AV-04, S-138
        raise BusinessRuleError("ZONE_NOT_FOUND", "La zona no existe.")
    if not consent:  # AV-05, S-133 (Ley 29733)
        raise BusinessRuleError("CONSENT_REQUIRED", "Sin el consentimiento del vecino no se guardan sus datos.")
    referred_by = find_by_referral(store, referral).customer_id if (referral or "").strip() else None  # AZ-05
    customer_id = max(store.customers, default=0) + 1  # S-135
    customer = Customer(customer_id, name, zone_id, phone=phone, consent_at=now, referred_by=referred_by, email=email)
    store.add_customer(customer)
    pin = new_pin()
    set_pin(store, customer_id, pin)
    return customer, pin


PIN_REQUEST_LIMIT = 100  # S-197


EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def normalize_email(email, store: InMemoryStore, *, except_id: int | None = None) -> str:
    """CR-01: formato, largo y unicidad sin importar mayúsculas."""
    text = (email or "").strip()
    if not text:
        raise BusinessRuleError("EMAIL_REQUIRED", "Escribe el correo del vecino.")
    if len(text) > 120 or not EMAIL_PATTERN.fullmatch(text):
        raise BusinessRuleError("INVALID_EMAIL", "Escribe un correo válido, por ejemplo nombre@gmail.com.")
    text = text.lower()
    if any(c.email == text and c.customer_id != except_id for c in store.customers.values()):
        raise BusinessRuleError("EMAIL_ALREADY_REGISTERED", "Ese correo ya está registrado.")
    return text


def parse_customer_number(user) -> int:
    """OP-05: solo se revisa el formato, no si el número existe."""
    text = str(user or "").strip()
    if not (text.isascii() and text.isdigit() and len(text) <= 9):
        raise BusinessRuleError("INVALID_INPUT", "Escribe tu número de cliente.")
    return int(text)


def request_pin_help(store: InMemoryStore, user, now: datetime) -> None:
    """OP-02..OP-05, S-196: no dice si el número existe; solo guarda la solicitud si corresponde."""
    customer_id = parse_customer_number(user)
    already_open = any(customer == customer_id for customer, _ in store.pin_requests.values())
    if customer_id not in store.customers or already_open or len(store.pin_requests) >= PIN_REQUEST_LIMIT:
        return
    store.pin_requests[max(store.pin_requests, default=0) + 1] = (customer_id, now)


def dismiss_pin_request(store: InMemoryStore, request_id: int, *, by: str) -> None:
    """OP-08, S-198."""
    _check_admin(store, by)
    if request_id not in store.pin_requests:
        raise BusinessRuleError("PIN_REQUEST_NOT_FOUND", "Esa solicitud ya no está.")
    del store.pin_requests[request_id]


def reset_pin(store: InMemoryStore, customer_id: int, *, by: str) -> str:
    """AV-07, S-137: PIN nuevo; una credencial nueva también quita el bloqueo."""
    _check_admin(store, by)
    if customer_id not in store.customers:
        raise BusinessRuleError("CUSTOMER_NOT_FOUND", "El cliente no está registrado.")
    pin = new_pin()
    set_pin(store, customer_id, pin)
    for request_id in [r for r, (customer, _) in store.pin_requests.items() if customer == customer_id]:  # OP-07
        del store.pin_requests[request_id]
    return pin
