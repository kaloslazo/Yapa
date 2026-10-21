"""Iteración 45: registro por invitación. Spec: docs/desarrollo/45-registro-por-invitacion.md.

El registro propio existe solo con el enlace de un vecino (S-236). Ninguna función mueve dinero.
"""

from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta

from . import notices
from .auth import _check_pin, set_pin
from .customers import check_phone, normalize_email
from .domain import MIN_ORDERS_PER_GROUP, BusinessRuleError, Customer
from .recovery import CODE_TTL, INVALID_CODE, MAX_ATTEMPTS, MAX_PER_HOUR, MIN_GAP, _digest
from .store import InMemoryStore

DAILY_LIMIT = 20  # S-239: registros por enlace en 24 horas
MAX_PENDING = 200  # S-239: registros a medio hacer
NOT_FOUND = ("INVITE_NOT_FOUND", "Ese enlace de invitación no existe o ya no vale. Pídele a tu vecino uno nuevo.")


def resolve(store: InMemoryStore, token) -> tuple[dict, Customer]:
    """IN-03, S-243: un código inventado, renovado o de un vecino suspendido da el mismo error."""
    invite = store.invites.get(str(token))
    inviter = store.customers.get(invite["customer_id"]) if invite and invite["active"] else None
    if inviter is None or inviter.suspended:
        raise BusinessRuleError(*NOT_FOUND)
    return invite, inviter


def _create(store: InMemoryStore, customer_id: int, now: datetime) -> str:
    token = secrets.token_urlsafe(8)  # S-237: al azar, no el código de referido
    store.invites[token] = {"customer_id": customer_id, "created": now, "active": True, "signups": []}
    return token


def _summary(store: InMemoryStore, token: str, customer_id: int, now: datetime) -> dict:
    done = [moment for invite in store.invites.values() if invite["customer_id"] == customer_id
            for moment in invite["signups"]]
    return {"codigo": token, "hoy": len([m for m in done if now - m < timedelta(days=1)]), "total": len(done)}


def link_for(store: InMemoryStore, customer_id: int, now: datetime) -> dict:
    """IN-01."""
    token = next((t for t, invite in store.invites.items() if invite["customer_id"] == customer_id and invite["active"]), None)
    return _summary(store, token or _create(store, customer_id, now), customer_id, now)


def renew(store: InMemoryStore, customer_id: int, now: datetime) -> dict:
    """IN-02, S-237."""
    for invite in store.invites.values():
        if invite["customer_id"] == customer_id:
            invite["active"] = False
    return _summary(store, _create(store, customer_id, now), customer_id, now)


def preview(store: InMemoryStore, token) -> dict:
    """IN-03: solo lo necesario para decidir; nada de apellido, celular ni correo."""
    _, inviter = resolve(store, token)
    zone = store.zones[inviter.zone_id]
    return {"zona": zone.name, "distrito": zone.district, "invita": (inviter.name.split() or [""])[0],
            "vecinos": len([c for c in store.customers.values() if c.zone_id == zone.zone_id]),
            "minimo_grupo": MIN_ORDERS_PER_GROUP}


def _check_limit(invite: dict, now: datetime) -> None:
    if len([moment for moment in invite["signups"] if now - moment < timedelta(days=1)]) >= DAILY_LIMIT:
        raise BusinessRuleError("INVITE_LIMIT", "Este enlace ya recibió muchos registros hoy. Inténtalo mañana.")


def _check_person(name: str, consent: bool) -> str:
    name = (name or "").strip()
    if not name:
        raise BusinessRuleError("NAME_REQUIRED", "Escribe tu nombre.")
    if not consent:
        raise BusinessRuleError("CONSENT_REQUIRED", "Sin tu consentimiento no podemos guardar tus datos.")
    return name


def start_signup(store: InMemoryStore, token, name, phone, email, consent: bool, now: datetime) -> tuple[str, str]:
    """IN-04: valida, guarda el registro a medio hacer y devuelve (correo, código) para enviarlo."""
    invite, inviter = resolve(store, token)
    _check_limit(invite, now)
    name = _check_person(name, consent)
    phone = check_phone(store, phone)
    email = normalize_email(email, store)
    for key in [key for key, record in store.signups.items() if now > record["expires"]]:
        del store.signups[key]
    record = store.signups.get(email)
    if record is None and len(store.signups) >= MAX_PENDING:
        raise BusinessRuleError("SIGNUPS_FULL", "Hay muchos registros en curso. Inténtalo en unos minutos.")
    recent = [moment for moment in (record or {"sent": []})["sent"] if now - moment < timedelta(hours=1)]
    if recent and now - max(recent) < MIN_GAP:
        raise BusinessRuleError("EMAIL_CODE_TOO_SOON", "Ya te mandamos un código hace un momento. Espera un minuto.")
    if len(recent) >= MAX_PER_HOUR:
        raise BusinessRuleError("EMAIL_CODE_LIMIT", "Pediste muchos códigos. Intenta de nuevo en una hora.")
    code, salt = f"{secrets.randbelow(10 ** 6):06d}", secrets.token_hex(8)
    store.signups[email] = {"name": name, "phone": phone, "inviter": inviter.customer_id, "consent_at": now,
                            "salt": salt, "digest": _digest(salt, code), "expires": now + CODE_TTL, "attempts": 0,
                            "sent": recent + [now]}
    return email, code


def _join(store: InMemoryStore, inviter: Customer, invite: dict, now: datetime, consent_at: datetime, **data) -> Customer:
    """IN-05, IN-06, IN-07, S-238, S-242: crea al vecino en la zona de quien invitó y avisa."""
    customer_id = max(store.customers, default=0) + 1
    customer = Customer(customer_id, zone_id=inviter.zone_id, referred_by=inviter.customer_id, consent_at=consent_at, **data)
    store.add_customer(customer)
    invite["signups"].append(now)
    notices.neighbor_joined(store, customer, inviter, store.zones[inviter.zone_id], now)
    return customer


def finish_signup(store: InMemoryStore, token, email, code, pin, now: datetime) -> Customer:
    """IN-05: el PIN se revisa antes de gastar el código; cualquier fallo del código da el mismo error."""
    invite, inviter = resolve(store, token)
    _check_pin(pin)
    key = str(email or "").strip().lower()
    record = store.signups.get(key)
    if not record or not record["digest"] or now > record["expires"] or record["inviter"] != inviter.customer_id:
        raise BusinessRuleError(*INVALID_CODE)
    if not hmac.compare_digest(record["digest"], _digest(record["salt"], str(code or "").strip())):
        record["attempts"] += 1
        if record["attempts"] >= MAX_ATTEMPTS:
            record["digest"] = None
        raise BusinessRuleError(*INVALID_CODE)
    _check_limit(invite, now)
    check_phone(store, record["phone"])
    normalize_email(key, store)
    record["digest"] = None
    customer = _join(store, inviter, invite, now, record["consent_at"], name=record["name"], phone=record["phone"],
                     email=key, email_verified_at=now)
    set_pin(store, customer.customer_id, pin)
    del store.signups[key]
    return customer


def signup_google(store: InMemoryStore, token, claims: dict, phone, consent: bool, now: datetime) -> Customer:
    """IN-06, S-240: el nombre y el correo vienen de Google; la cuenta nace sin PIN."""
    invite, inviter = resolve(store, token)
    _check_limit(invite, now)
    phone = check_phone(store, phone)
    if not consent:
        raise BusinessRuleError("CONSENT_REQUIRED", "Sin tu consentimiento no podemos guardar tus datos.")
    email = normalize_email(claims["email"], store)
    if any(c.google_sub == claims["sub"] for c in store.customers.values()):
        raise BusinessRuleError("GOOGLE_ALREADY_LINKED", "Esa cuenta de Google ya está vinculada a otro vecino.")
    name = (claims.get("name") or "").strip() or email.split("@")[0]
    return _join(store, inviter, invite, now, now, name=name, phone=phone, email=email, email_verified_at=now,
                 google_sub=claims["sub"])
