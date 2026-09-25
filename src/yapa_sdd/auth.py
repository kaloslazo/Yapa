"""Acceso con PIN (vecinos) y contraseña (administrador) (iteración 10).

Spec: docs/desarrollo/10-acceso.md. Nunca se guarda el secreto, solo su hash con sal (S-67).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from .domain import BusinessRuleError
from .store import InMemoryStore


ITERATIONS = 200_000  # S-67
MAX_FAILURES = 5  # S-68
LOCK_TIME = timedelta(minutes=15)
MIN_ADMIN_PASSWORD = 10  # S-70


@dataclass
class Credential:
    salt: bytes
    hash: bytes
    failures: int = 0
    locked_until: datetime | None = None


def _hash(secret: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, ITERATIONS)


def _new_credential(secret: str) -> Credential:
    salt = os.urandom(16)
    return Credential(salt, _hash(secret, salt))


def _check_pin(pin: str) -> None:
    """S-64 y S-66: 6 dígitos, no todos iguales y sin secuencias."""
    if not re.fullmatch(r"\d{6}", pin or ""):
        raise BusinessRuleError("INVALID_PIN", "El PIN debe tener exactamente 6 dígitos.")
    steps = {int(b) - int(a) for a, b in zip(pin, pin[1:])}
    if steps in ({0}, {1}, {-1}):
        raise BusinessRuleError("INVALID_PIN", "Ese PIN es muy fácil de adivinar; elige otro.")


def set_pin(store: InMemoryStore, customer_id: int, pin: str) -> None:
    """AC-01: el administrador asigna el PIN inicial (S-65)."""
    if customer_id not in store.customers:
        raise BusinessRuleError("CUSTOMER_NOT_FOUND", "El cliente no está registrado.")
    _check_pin(pin)
    store.credentials[("vecino", str(customer_id))] = _new_credential(pin)


def set_admin_password(store: InMemoryStore, admin_id: str, password: str) -> None:
    if len(password or "") < MIN_ADMIN_PASSWORD:
        raise BusinessRuleError("INVALID_PASSWORD", f"La contraseña debe tener al menos {MIN_ADMIN_PASSWORD} caracteres.")
    store.admins.add(admin_id)
    store.credentials[("admin", admin_id)] = _new_credential(password)


def authenticate(store: InMemoryStore, kind: str, user, secret: str, now: datetime):
    """AC-02 y AC-03. Devuelve el número de cliente (vecino) o el usuario (admin)."""
    key = (kind, str(user).strip())
    credential = store.credentials.get(key)
    if credential is None:
        _hash(secret or "", b"\0" * 16)  # mismo costo: no revela si el usuario existe
        raise BusinessRuleError("INVALID_CREDENTIALS", "Usuario o clave incorrectos.")
    if credential.locked_until and now < credential.locked_until:
        raise BusinessRuleError("ACCOUNT_LOCKED", "Demasiados intentos. Vuelve a intentar en 15 minutos.")
    if not hmac.compare_digest(_hash(secret or "", credential.salt), credential.hash):
        credential.failures += 1
        if credential.failures >= MAX_FAILURES:
            credential.failures = 0
            credential.locked_until = now + LOCK_TIME
        raise BusinessRuleError("INVALID_CREDENTIALS", "Usuario o clave incorrectos.")
    credential.failures = 0
    credential.locked_until = None
    return int(key[1]) if kind == "vecino" else key[1]


def change_pin(store: InMemoryStore, customer_id: int, current: str, new: str, now: datetime) -> None:
    """AC-01 / S-65: el vecino cambia su PIN indicando el actual."""
    authenticate(store, "vecino", customer_id, current, now)
    set_pin(store, customer_id, new)
