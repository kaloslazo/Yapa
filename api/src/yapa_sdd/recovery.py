"""Iteración 40: correo del vecino, verificación y recuperación del PIN con un código.

Spec: docs/desarrollo/40-correo-y-recuperar-pin.md. Los códigos no se guardan en claro (CR-07, S-207).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import replace
from datetime import datetime, timedelta

from .auth import _check_pin, set_pin
from .customers import normalize_email, parse_customer_number, request_pin_help
from .domain import BusinessRuleError
from .store import InMemoryStore

CODE_TTL = timedelta(minutes=10)  # S-203
MAX_ATTEMPTS = 5
MIN_GAP = timedelta(seconds=60)
MAX_PER_HOUR = 5
INVALID_CODE = ("INVALID_CODE", "El código no es válido o ya venció. Pide uno nuevo.")


def mask_email(email: str | None) -> str | None:
    """CR-08: a***@gmail.com."""
    if not email:
        return None
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}"


def _digest(salt: str, code: str) -> str:
    return hashlib.sha256((salt + code).encode("utf-8")).hexdigest()


def _issue_code(store: InMemoryStore, customer_id: int, purpose: str, now: datetime) -> str:
    """CR-04, S-203: un código nuevo reemplaza al anterior; respeta el reenvío mínimo y el tope por hora."""
    record = store.email_codes.get((customer_id, purpose), {"sent": []})
    recent = [moment for moment in record["sent"] if now - moment < timedelta(hours=1)]
    if recent and now - max(recent) < MIN_GAP:
        raise BusinessRuleError("EMAIL_CODE_TOO_SOON", "Ya te mandamos un código hace un momento. Espera un minuto.")
    if len(recent) >= MAX_PER_HOUR:
        raise BusinessRuleError("EMAIL_CODE_LIMIT", "Pediste muchos códigos. Intenta de nuevo en una hora.")
    code = f"{secrets.randbelow(10 ** 6):06d}"
    salt = secrets.token_hex(8)
    store.email_codes[(customer_id, purpose)] = {"salt": salt, "digest": _digest(salt, code), "expires": now + CODE_TTL,
                                                  "attempts": 0, "sent": recent + [now]}
    return code


def _consume_code(store: InMemoryStore, customer_id: int, purpose: str, code, now: datetime) -> None:
    """CR-04: vence a los 10 minutos y se agota a los 5 intentos; un código bueno se gasta."""
    record = store.email_codes.get((customer_id, purpose))
    if not record or not record["digest"] or now > record["expires"]:
        raise BusinessRuleError(*INVALID_CODE)
    if not hmac.compare_digest(record["digest"], _digest(record["salt"], str(code or "").strip())):
        record["attempts"] += 1
        if record["attempts"] >= MAX_ATTEMPTS:
            record["digest"] = None
        raise BusinessRuleError(*INVALID_CODE)
    record["digest"] = None


def start_email_verification(store: InMemoryStore, customer_id: int, email, now: datetime) -> tuple[str, str]:
    """CR-02: guarda el correo (sin verificar) y devuelve (correo, código) para enviarlo."""
    clean = normalize_email(email, store, except_id=customer_id)
    code = _issue_code(store, customer_id, "verificar", now)
    store.customers[customer_id] = replace(store.customers[customer_id], email=clean, email_verified_at=None)
    return clean, code


def confirm_email(store: InMemoryStore, customer_id: int, code, now: datetime) -> None:
    """CR-03."""
    if not store.customers[customer_id].email:
        raise BusinessRuleError(*INVALID_CODE)
    _consume_code(store, customer_id, "verificar", code, now)
    store.customers[customer_id] = replace(store.customers[customer_id], email_verified_at=now)


def request_pin_reset(store: InMemoryStore, user, now: datetime) -> tuple[str, str] | None:
    """CR-05: con correo verificado devuelve (correo, código); si no, deja la solicitud para el equipo."""
    customer_id = parse_customer_number(user)
    customer = store.customers.get(customer_id)
    if customer is not None and customer.email and customer.email_verified_at:
        try:
            return customer.email, _issue_code(store, customer_id, "recuperar", now)  # S-209: los límites no se avisan
        except BusinessRuleError:
            return None
    request_pin_help(store, user, now)
    return None


def reset_pin_with_code(store: InMemoryStore, user, code, new_pin, now: datetime) -> None:
    """CR-06: cualquier fallo del código da el mismo error (S-205); el PIN se revisa antes y no gasta el código."""
    _check_pin(new_pin)
    try:
        customer_id = parse_customer_number(user)
    except BusinessRuleError:
        raise BusinessRuleError(*INVALID_CODE) from None
    customer = store.customers.get(customer_id)
    if customer is None or not (customer.email and customer.email_verified_at):
        raise BusinessRuleError(*INVALID_CODE)
    _consume_code(store, customer_id, "recuperar", code, now)
    set_pin(store, customer_id, new_pin)  # una credencial nueva también quita el bloqueo (S-207)
    for request_id in [r for r, (customer_, _) in store.pin_requests.items() if customer_ == customer_id]:
        del store.pin_requests[request_id]
