"""Semana de demo (S-141..S-143): la 2026-W39 entregada y liquidada, y la 2026-W40 abierta con pedidos.

Todo se hace con los casos de uso, en el orden de una semana real, para que la conciliación dé 0.
Spec: docs/desarrollo/25-presentacion-web.md.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from decimal import Decimal as D

from . import auth, cycle, fulfillment, persistence, purchase, reference
from .cycle import LIMA
from .domain import BusinessRuleError, Customer, Zone
from .order_registration import quote_order, register_order, verify_payment
from .seed import pilot_store
from .store import InMemoryStore


DEMO_NOW = datetime(2026, 9, 30, 10, 0, tzinfo=LIMA)  # S-143: miércoles, ciclo 2026-W40 abierto
ADMIN = "admin-yapa"
DEBUG_ADMIN = "debug-global"  # S-256

W39_WEDNESDAY = datetime(2026, 9, 23, 10, 0, tzinfo=LIMA)
W39_PRICES_SEEN = datetime(2026, 9, 24, 18, 0, tzinfo=LIMA)
W39_SATURDAY = datetime(2026, 9, 26, 10, 0, tzinfo=LIMA)

# Vecinos ficticios (S-141)
DEMO_CUSTOMERS = [
    Customer(106, "Lucía Ramos", "Z-LINCE-01"),
    Customer(107, "Pedro Huamán", "Z-LINCE-01"),
    Customer(108, "Elena Vargas", "Z-LINCE-01"),
    Customer(109, "Miguel Chávez", "Z-LINCE-01"),
    Customer(110, "Sofía Mendoza", "Z-LINCE-01"),
    Customer(111, "Raúl Paredes", "Z-LINCE-01"),
    Customer(112, "Teresa Flores", "Z-LINCE-01"),
    Customer(113, "Julio Castro", "Z-JM-01"),
    Customer(114, "Rosa Medina", "Z-JM-01"),
]

BASKETS = [
    {"PAPA-AMARILLA": "5", "PAPA-BLANCA": "10", "CEBOLLA-ROJA": "10"},
    {"PAPA-AMARILLA": "8", "CEBOLLA-ROJA": "5", "LIMON": "4", "AJO": "1", "ZANAHORIA": "5"},
    {"PAPA-BLANCA": "10", "CAMOTE": "6", "ZANAHORIA": "6", "LIMON": "3", "LIMPIATODO-GALON": "2"},
    {"PAPA-AMARILLA": "6", "CEBOLLA-ROJA": "6", "AJO": "0.5", "DETERGENTE-LIQUIDO-GALON": "1"},
]

# Plaza Vea, 24/09/2026 (docs/analisis/08_validacion_economica.md). Sin precios de mercado: no se midieron.
SUPERMARKET = {"PAPA-BLANCA": "2.39", "PAPA-AMARILLA": "7.99", "CEBOLLA-ROJA": "3.89", "AJO": "16.49",
               "LIMON": "4.29", "CAMOTE": "3.39", "ZANAHORIA": "3.69"}


def _order(store: InMemoryStore, customer_id: int, basket: dict, now: datetime):
    lines = list(basket.items())
    total = quote_order(store, lines).total
    return register_order(store, customer_id=customer_id, lines=lines, payment_method="YAPE",
                          operation_code=f"DEMO-{now:%V}-{customer_id}", amount=total, now=now)


def demo_clock(store: InMemoryStore):
    """DM-04, S-254: el momento de la demostración que la base guardó, o nada si no es una base de demostración."""
    return store.demo_now


def demo_store(now: datetime | None = None) -> InMemoryStore:
    """DM-01: sin `now`, la de septiembre de siempre; con `now`, corrida a la semana de `now` (S-253)."""
    weeks = round((cycle.opens_at(cycle.cycle_id(now)) - cycle.opens_at(cycle.cycle_id(DEMO_NOW))).days / 7) if now else 0
    shift = timedelta(weeks=weeks)
    cycle39, cycle40 = cycle.add_weeks("2026-W39", weeks), cycle.add_weeks("2026-W40", weeks)
    demo_now, w39_wednesday, w39_prices_seen, w39_saturday = DEMO_NOW + shift, W39_WEDNESDAY + shift, W39_PRICES_SEEN + shift, W39_SATURDAY + shift
    store = pilot_store()
    for customer in DEMO_CUSTOMERS:
        store.add_customer(customer)

    # Semana 2026-W39: Lince llega al mínimo; Jesús María no (vuelve todo)
    w39 = [101, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
    for i, customer_id in enumerate(w39):
        order = _order(store, customer_id, BASKETS[i % len(BASKETS)], w39_wednesday)
        verify_payment(store, order.order_id, now=w39_wednesday)
    for product_id, price in SUPERMARKET.items():
        reference.register_reference(store, product_id, "SUPERMERCADO", D(price), "Plaza Vea", date(2026, 9, 24) + shift,
                                     by=ADMIN, now=w39_prices_seen)
    for order in store.orders_in_cycle(cycle39):
        if fulfillment.is_attended(store, order):
            fulfillment.pack_bag(store, order.order_id, by=ADMIN, photo=f"fotos/w39-pedido-{order.order_id}.jpg",
                                 now=w39_saturday)
    purchase.register_purchase(store, cycle39, {}, by=ADMIN, now=w39_saturday)  # S-299: llegó todo
    fulfillment.deliver_zone(store, cycle39, "Z-LINCE-01", by=ADMIN, photo="fotos/w39-entrega-alamos.jpg",
                             received_by="Portería Los Álamos", now=w39_saturday)
    fulfillment.close_cycle(store, cycle39, at=w39_saturday)

    # Desde la 2026-W40, Ana (101) organiza Los Álamos (AZ-01, AZ-02) e invitó a Diana (AZ-06)
    alamos = store.zones["Z-LINCE-01"]
    alamos.admin_id, alamos.created_cycle = 101, cycle40
    alamos.reception_kind, alamos.reception_contact = "PORTERIA", "Portería Los Álamos"
    store.add_customer(Customer(115, "Diana Rojas", "Z-LINCE-01", referred_by=101))

    # S-188: otro edificio de Lince con su propio admin (Marta, 116), a 391 m de Los Álamos y 455 m de Las Palmeras
    arenales = Zone("Z-LINCE-03", "Edificio Arenales", "Lince", "G-LINCE-3", D("40"), lat=-12.0852, lon=-77.0375,
                    admin_id=116, reception_kind="PORTERIA", reception_contact="Portería Arenales", created_cycle=cycle40)
    store.zones[arenales.zone_id] = arenales
    store.add_customer(Customer(116, "Marta Quispe", "Z-LINCE-03"))

    # Semana 2026-W40, abierta: Ana (101) queda libre para pedir en vivo
    for i, customer_id in enumerate([105, 106, 107, 108, 109, 110, 115]):
        order = _order(store, customer_id, BASKETS[(i + 1) % len(BASKETS)], demo_now)
        if i < 4:
            verify_payment(store, order.order_id, now=demo_now)
    store.demo_now = demo_now if now else None
    return store


def parse_demo_pins(text: str) -> dict:
    """S-255: "101=123450,105=739104,116=260318" -> {101: "123450", ...}."""
    pins = {}
    for part in (text or "").split(","):
        customer, _, pin = part.partition("=")
        if customer.strip().isdigit() and pin.strip():
            pins[int(customer)] = pin.strip()
    return pins


NEEDED_PINS = (101, 105, 116)  # Ana (admin de zona), Carmen (vecina) y Marta (admin de zona)


def seed_demo_base(path: str, now: datetime, pins: dict, debug_password: str) -> InMemoryStore:
    """DM-03, S-253..S-256: crea la base de demostración de la semana de `now` con las cuentas de prueba."""
    if Path(path).exists():
        raise BusinessRuleError("DATABASE_EXISTS", "Esa base ya existe: no se pisa. Bórrala si quieres sembrarla de nuevo.")
    if any(customer not in pins for customer in NEEDED_PINS):
        raise BusinessRuleError("DEMO_PINS_REQUIRED", "Faltan PIN para las cuentas de prueba (101, 105 y 116).")
    for customer in NEEDED_PINS:
        auth._check_pin(pins[customer])
    if len(debug_password or "") < auth.MIN_ADMIN_PASSWORD:
        raise BusinessRuleError("INVALID_PASSWORD", f"La clave del admin global debe tener al menos {auth.MIN_ADMIN_PASSWORD} caracteres.")
    store = demo_store(now)
    for customer in NEEDED_PINS:
        auth.set_pin(store, customer, pins[customer])
    auth.set_admin_password(store, DEBUG_ADMIN, debug_password)
    store.debug_admins.add(DEBUG_ADMIN)
    persistence.save(store, path)
    return store
